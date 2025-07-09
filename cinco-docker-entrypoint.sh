#!/bin/bash
set -e

# Remove lock file. This can stick around if solr was not shut down properly.
if [ -f "/var/solr/data/arclight/data/index/write.lock" ]; then
    rm /var/solr/data/arclight/data/index/write.lock
fi

# Run script to configure as leader/follower for solr index replication
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

# Run helper script to initialize an empty solr
init-var-solr

coredir="/var/solr/data/arclight"
config_source="/opt/solr/server/solr/configsets/arclight"
if [[ ! -d $coredir ]]; then
    # pre-create core
    cp -r "$config_source/." "$coredir/"
    touch "$coredir/core.properties"
    echo "Created $CORE"
else
    # copy current config into place even if core already exists
    cp -r "$config_source/." "$coredir/"
    echo "Core $CORE already exists"
fi

# start solr
exec solr-fg