#!/bin/bash
set -euo pipefail

if [[ "$REPLICATION_ROLE" == "leader" ]]; then
    cron
else
    rm -rf /etc/cron.d/leader-backup.cron /opt/solr/docker/scripts/leader-backup
fi

exec gosu solr bash /solr-setup.sh
