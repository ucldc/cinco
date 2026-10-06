#!/bin/bash
set -euo pipefail

if [[ "$REPLICATION_ROLE" == "leader" ]]; then
    cron
else
    rm -rf /etc/cron.d/leader-backup.cron /opt/solr/arclight/leader-backup.py
fi

exec gosu solr bash /opt/solr/arclight/solr-setup.sh
