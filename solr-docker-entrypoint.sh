#!/bin/bash
set -e

# add leader or follower configuration using solr's Config API
if [[ $REPLICATION_ROLE = 'leader' ]] ; then
    curl -X POST -H 'Content-type:application/json' -d '{
    "add-requesthandler": {
        "name": "/replication",
        "class": "solr.ReplicationHandler",
        "leader": {
            "replicateAfter": "commit",
            "backupAfter": "optimize",
            "confFiles": "schema.xml,stopwords.txt,elevate.xml"
        },
        "maxNumberOfBackups": 2,
        "commitReserveDuration": "00:00:10",
        "invariants": {
            "maxWriteMBPerSec": "16"
        }
    }
    }' http://localhost:8983/api/collections/techproducts/config
elif [[ $REPLICATION_ROLE = 'follower' ]] ; then
    curl -X POST -H 'Content-type:application/json' -d '{
    "add-requesthandler": {
        "name": "/replication",
        "class": "solr.ReplicationHandler",
        "follower": {
            "leaderUrl": "http://solr_leader:8983/solr/arclight/replication",
            "pollInterval": "00:00:20"
        }
    }' http://localhost:8983/api/collections/techproducts/config
fi

# create and start solr core
exec solr-precreate arclight /opt/solr/server/solr/configsets/arclight
