#!/bin/bash
set -e

# create a log message function that takes a status, a message, and a solr resp, and outputs a JSON object with those values
log_msg() {
    local arclight_replication_status="$1"
    local message="$2"
    local solr_resp="$3"
    echo "log_msg"
    jq -nc --arg arclight_replication_status "$arclight_replication_status" --arg message "$message" --argjson solr_resp "$solr_resp" '$ARGS.named'
}

coredir="/var/solr/data/arclight"
config_source="/opt/solr/server/solr/configsets/arclight"
if [[ ! -d $coredir ]]; then
    # pre-create core
    cp -r "$config_source/." "$coredir/"
    touch "$coredir/core.properties"
    echo "Created $CORE"
    created="true"
else
    # copy current config into place even if core already exists
    cp -r "$config_source/." "$coredir/"
    echo "Core $CORE already exists"
fi

# Restore from backup if this instance is a follower, or if we're creating the core for the first time
if [[ "$REPLICATION_ROLE" == "follower" || "${created:-}" == "true" ]]; then
    echo "Replication role is $REPLICATION_ROLE; restoring from backup snapshot"

    # start solr, wait for it to be fully up and ready, and then perform restore
    solr start
    /opt/solr/docker/scripts/wait-for-solr.sh --max-attempts 30 --solr-url http://localhost:8983/solr

    # poll till the core is loaded
    start_time=$(date +%s)
    timeout_seconds=60
    polling_seconds=5
    while true; do
        solr_resp=$(curl -s "http://localhost:8983/solr/admin/cores?action=status&core=arclight")
        echo $solr_resp
        is_loaded=$(echo "$solr_resp" | jq -r '.status.arclight.isLoaded')
        is_loading=$(echo "$solr_resp" | jq -r '.status.arclight.isLoading')
        index_num_docs=$(echo "$solr_resp" | jq -r '.status.arclight.index.numDocs')
        if [[ "$is_loaded" == "false" && "$is_loading" == "true" ]]; then
            sleep $polling_seconds
        elif [[ "$is_loaded" == "true" || "$index_num_docs" == 0 ]]; then
            break
        else
            echo $(log_msg "failed" "unexpected core status" "$solr_resp")
            exit 1
        fi

        # if the timeout has been reached, log a message and exit
        now=$(date +%s)
        elapsed=$(( now - start_time ))
        if (( elapsed >= 60 )); then
            echo $(log_msg "failed" "core did not come up within ${timeout_seconds}s" "$solr_resp")
            break
        fi
    done

    # restore from backup
    solr_resp=$(curl -s "http://localhost:8983/solr/arclight/replication?command=restore&repository=s3&location=solr_backups")
    echo $solr_resp
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
        echo $solr_resp
        restorestatus=$(echo "$solr_resp" | jq -r '.restorestatus')
        status=$(echo "$restorestatus" | jq -r '.status')

        if [[ "$status" == "success" ]]; then
            echo $(log_msg $status "Restore completed successfully" "$solr_resp")
            break
        elif [[ "$status" == "failed" ]]; then
            echo $(log_msg $status "Solr restore failed - see solr response for details" "$solr_resp")
            exit 1
        else
            sleep $polling_seconds
        fi

        # if the timeout has been reached, log a message and exit
        now=$(date +%s)
        elapsed=$(( now - start_time ))
        if (( elapsed >= timeout_seconds )); then
            echo $(log_msg $status "restore did not complete within ${timeout_seconds}s" "$solr_resp")
            break
        fi
    done

    solr stop
fi

# Run script to configure as leader/follower for solr index replication
if [ "$REPLICATION_ROLE" != "" ]; then
    python3 /opt/solr/arclight/solr-replication-config.py
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
