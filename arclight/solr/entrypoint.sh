#!/bin/bash
set -euo pipefail

if [[ "$REPLICATION_ROLE" == "leader" ]]; then

    OPTIONAL_CRON_VARS=(
        AWS_ACCESS_KEY_ID
        AWS_SECRET_ACCESS_KEY
        AWS_REGION
        SOLR_S3_ENDPOINT
        SOLR_S3_BUCKET
    )
    for var in "${OPTIONAL_CRON_VARS[@]}"; do
        if [ -n "${!var-}" ]; then
            echo "$var=\"${!var}\"" >> /etc/environment
        fi
    done

    cron
else
    rm -rf /etc/cron.d/leader-backup.cron /opt/solr/arclight/leader-backup.py
fi

exec gosu solr bash /opt/solr/arclight/solr-setup.sh
