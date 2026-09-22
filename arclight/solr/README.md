# Arclight Solr

We run several standalone Solr instances, not Solr Cloud. Our indexing load is pretty low - it can spike when a contributor is actively updating their EADs, though. Since EAD components are indexed as their own documents,

## Leader/Follower Architecture

We have 1 leader Solr instance running in ECS with an EFS backed filesystem. Index updates go through this leader. We have multiple follower instances running in ECS and using the ephemeral filesystem to store the index. Follower instances are spun up and caught (mostly) up-to-date from an index backup stored in s3. Then replication is started on the follower, and more recent updates are propagated to the follower via replication.

### Replication

Replication happens at request of the follower, rather than at issuance of the leader. In `solr-replication-config.py`, the follower is configured to poll the leader every 20 seconds for any updates - this results in an update latency of at most 20 seconds from leader to follower of - critically - any *hard commits*. Soft commits are *not* replicated (more on commits later).

### Backups

#### Backup Creation on the Leader

Backups are exclusively taken of the leader - how is still under consideration.

> We can't use solr's auto backup - it can only be configured to happen on `optimize`, `commit`, or `startup` and none of these three are good options for us. We never optimize (hence removing replicateAfter and backupAfter optimize in this commit); when we actually get a workload, commits might happen too frequently and backups happening alongside the commits might overwhelm the leader; startup happens very, very rarely. Additionally, there is no option in the replicationHandler to add the configured s3 repository and location - the auto backup exclusively uses the local filesystem.

Option 1: Eventbridge Scheduler > Run Task > One-Off Run Task with security group permissions allowing requests to http://solr-leader:8983/solr/arclight/replication? endpoint. The ArcLight image already has this security group...could add a script to the image and override the entrypoint command? Seems odd that the ArcLight image would have the solr backup script, though. Could also put the solr backup script in the solr image and override the entrypoint?

Option 2: Sidecar container defined in the task definition that does nothing but run cron (Dockerfile.cron), with network permissions to hit http://solr-leader:8983/solr/arclight/replication? endpoint - in awsvpc mode (which we use), no special permissions necessary - all handled by ECS magic. Hooray.

Option 3 (currently implemented): Running cron on the solr container itself. Involves some trickiness regarding starting the container as root so we can start cron as root and then dropping into the solr user to run solr. Also some trickiness regarding backup script output tailed into the solr logs themselves. But also this kind of seems like the right place for it?

#### Backup Utilization on the Followers

Backups are used to pre-populate followers in `solr-setup.sh` using the replication API with command=restore. In order to use Solr's replication API, Solr must be actively running, however, we do want to use the restore command to pre-populate prior to initiating replication (or else, replication will start from the very beginning of the solr index's history, and will cause the follower to hit the leader excessively), so we spin up Solr, restore from backup, stop Solr, update the configuration to enable replication polling, and then restart Solr again.

### Commits

Configured in `solrconfig.xml`

Hard commits (writing the data to disk) are made every 60 seconds, or after 10,000 documents, or after the transaction log exceeds 512 MB. Since soft commits - which make data visible to the searcher - are disabled, we do open a new searcher when we issue a hard commit.

> Since it is only hard commits that are replicated to followers, we can deduce that the maximum latency between a document getting indexed to the leader and the leader writing the data to disk is 60 seconds, and the maximum latency between the leader issuing a hard commit and the follower learning of this new hard commit is 20 seconds. This doesn't count the actual time it takes the leader to make the hard commit, the time it takes the follower to retrieve the data, or the time it takes the follower to open a new searcher once it has retrieved the data, but given that our indexing load is low, hard commits should be mere seconds, and follower replication data retrieval should also be mere seconds. Opening a new searcher can take a bit longer, but I think it's generous and safe to say there should be a maximum of 2 minutes between indexing the document to the leader and the document being found on the follower. **This does not take into account any application-level or CloudFront level caching, though**

Soft commits are disabled - since the leader is rarely handling search queries (only manually by a developer), only updates, there is no clear use for soft commits. In fact, it is safer to keep soft commits turned off for the occasional bulk workloads.

~~Soft commits are made every 30 seconds, these soft commits make data visible to the searcher (hence, we don't need to open a new searcher when we issue a hard commit). However, soft commits don't write data to disk, the data is still stored in the transaction log.~~

### Soft Commits & Bulk Indexing

**If at some point we turn soft commits back on:**

For bulk indexing, use the API to disable soft commits! Otherwise, our transaction log will get very large!

```sh
curl -X POST -H 'Content-type:application/json' \
-d '{
  "set-property": {
    "updateHandler.autoSoftCommit.maxTime": -1
  }
}' \
http://localhost:8983/solr/arclight/config

# verify configuration has updated
curl http://localhost:8983/solr/arclight/config/overlay
```

Then, after finishing bulk indexing, manually hard commit, and enable soft commits again:

```sh
curl "http://localhost:8983/solr/arclight/update?commit=true"

# re-enable soft commits
curl -X POST -H 'Content-type:application/json' \
-d '{
  "set-property": {
    "updateHandler.autoSoftCommit.maxTime": 30000
  }
}' \
http://localhost:8983/solr/arclight/config
# verify configuration has updated
curl http://localhost:8983/solr/arclight/config/overlay
```
