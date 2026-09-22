#!/bin/bash
set -e

# create a log message function that takes a status, a message, and a solr resp, and outputs a JSON object with those values
log_msg() {
    local arclight_backup_status="$1"
    local message="$2"
    local solr_resp="$3"
    jq -nc --arg arclight_backup_status "$arclight_backup_status" --arg message "$message" --argjson solr_resp "$solr_resp" '$ARGS.named'
}

# Remove lock file. This can stick around if solr was not shut down properly.
if [ -f "/var/solr/data/arclight/data/index/write.lock" ]; then
    rm /var/solr/data/arclight/data/index/write.lock
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

if [[ "$REPLICATION_ROLE" == "follower" ]]; then
    echo "Replication role is $REPLICATION_ROLE; restoring from backup snapshot"

    # start solr, wait for it to be fully up and ready, and then perform restore
    solr start
    /opt/solr/docker/scripts/wait-for-solr.sh --max-attempts 30 --solr-url http://localhost:8983/solr

    # restore from backup
    solr_resp=$(curl -s "http://localhost:8983/solr/arclight/replication?command=restore&repository=s3&location=solr_backups")
    respstatus=$(echo "$solr_resp" | jq -r '.status')
    if [[ "$respstatus" != "OK" ]]; then
        echo $(log_msg "failed" "error issuing replication?command=restore" "$solr_resp")
        exit 1
    fi

    # wait up to {timeout} for restore to complete successfully, checking every {polling} seconds
    start_time=$(date +%s)
    timeout_seconds=60
    polling_seconds=5
    while true; do
        # curl for details on the restore status
        solr_resp=$(curl -s "http://localhost:8983/solr/arclight/replication?command=restorestatus")
        restorestatus=$(echo "$solr_resp" | jq -r '.restorestatus')
        status=$(echo "$restorestatus" | jq -r '.status')

        if [[ "$status" == "success" ]]; then
            echo $(log_msg $status "Restore completed successfully" "$restorestatus")
            break
        elif [[ "$status" == "failed" ]]; then
            echo $(log_msg $status "Solr backup failed - see solr response for details" "$solr_resp")
            exit 1
        else
            sleep $polling_seconds
        fi

        # if the timeout has been reached, log a message and exit
        now=$(date +%s)
        elapsed=$(( now - start_time ))
        if (( elapsed >= timeout_seconds )); then
            echo $(log_msg $status "backup did not complete within ${timeout_seconds}s" "$solr_resp")
            break
        fi
    done

    solr stop
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

# start solr while also tailing leader-backup logs
touch /tmp/leader-backup
tail -F /tmp/leader-backup &
exec solr-fg
