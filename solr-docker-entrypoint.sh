#!/bin/bash
set -e

if [ "$REPLICATION_ROLE" != "" ]; then
    python3 /solr-replication-config.py
    if [[ "$?" != 0 ]]; then
        echo "Error running solr-replication-config.py"
        exit 1
    else
        echo "Configured solr for replication role: $REPLICATION_ROLE"
    fi
else
    echo "REPLICATION_ROLE env var not set; skipping configuration for solr index replication."
fi

# create and start solr core
exec solr-precreate arclight /opt/solr/server/solr/configsets/arclight
