# Arclight Solr

We run several standalone Solr instances, not Solr Cloud. Our indexing load is pretty low - it can spike when a contributor is actively updating their EADs, though. Since EAD components are indexed as their own documents,

## Leader/Follower Architecture

We have 1 leader Solr instance running in ECS with an EFS backed filesystem. Index updates go through this leader. We have multiple follower instances running in ECS and using the ephemeral filesystem to store the index. Follower instances are spun up and caught (mostly) up-to-date from an index backup stored in s3. Then replication is started on the follower, and more recent updates are propagated to the follower via replication.

### Replication

Replication happens at request of the follower, rather than at issuance of the leader. In `solr-replication-config.py`, the follower is configured to poll the leader every 20 seconds for any updates - this results in an update latency of at most 20 seconds from leader to follower.

### Backups

Backups are exclusively taken of the leader - still trying to figure out how.

> Can't use solr's auto backup - it can only be configured to happen on `optimize`, `commit`, or `startup` and none of these three are good options for us. We never optimize (hence removing replicateAfter and backupAfter optimize in this commit); when we actually get a workload, commits might happen too frequently and backups happening alongside the commits might overwhelm the leader; startup happens very, very rarely. Additionally, there is no option in the replicationHandler to add the configured s3 repository and location - the auto backup exclusively uses the local filesystem.

Backups are used to pre-populate followers in `cinco-docker-entrypoint.sh` using the replication API with command=restore. In order to use Solr's replication API, Solr must be actively running, however, we do want to use the restore command to pre-populate prior to initiating replication (or else, replication will start from the very beginning of the solr index's history, and will cause the follower to hit the leader excessively), so we spin up Solr, restore from backup, stop Solr, update the configuration to enable replication polling, and then restart Solr again.

### Commits

Configured in `solrconfig.xml`

Hard commits (writing the data to disk) are made every 60 seconds, or after 10,000 documents, or after the transaction log exceeds 512 MB. We don't open a new searcher when we issue a hard commit.

Soft commits are made every 30 seconds, these soft commits make data visible to the searcher (hence, we don't need to open a new searcher when we issue a hard commit). However, soft commits don't write data to disk, the data is still stored in the transaction log.

### Bulk indexing

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
