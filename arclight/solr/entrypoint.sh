#!/bin/bash
set -euo pipefail

if [[ "$REPLICATION_ROLE" == "leader" ]]; then
    cron
else
    rm -rf /etc/cron.d/leader-backup.cron
fi

exec gosu solr bash /cinco-docker-entrypoint.sh
