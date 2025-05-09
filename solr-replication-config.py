"""
Update solrconfig.xml for index replication
See https://solr.apache.org/guide/solr/latest/deployment-guide/user-managed-index-replication.html

This script is pretty dumb, and simply inserts the relevant configuration before the last line
of the solrconfig.xml file
"""

import os

solrconfig_path = "/opt/solr/server/solr/configsets/arclight/conf/solrconfig.xml"
with open(solrconfig_path, "r") as f:
    solr_config = [line for line in f]

if solr_config[-1].strip() == "":
    solr_config = solr_config[-1]

if solr_config[-1].strip() != "</config>":
    raise ValueError("Last line of solrconfig.xml is not '</config>'")

leader_config = [
    "  <!-- leader configuration for index replication -->\n"
    '  <requestHandler name="/replication" class="solr.ReplicationHandler">\n',
    '    <lst name="leader">\n',
    '      <str name="replicateAfter">optimize</str>\n',
    '      <str name="backupAfter">optimize</str>\n',
    '      <str name="confFiles">_rest_managed.json,elevate.xml,mapping-ISOLatin1Accent.txt,protwords.txt,schema.xml,scripts.conf,spellings.txt,stopwords_en.txt,stopwords.txt,synonyms.txt</str>\n',
    "    </lst>\n",
    '    <int name="maxNumberOfBackups">2</int>\n',
    '    <str name="commitReserveDuration">00:00:10</str>\n',
    '    <lst name="invariants">\n',
    '      <str name="maxWriteMBPerSec">16</str>\n',
    "    </lst>\n",
    "  </requestHandler>\n\n",
]

remote_host = "solr_leader"
follower_config = [
    "  <!-- follower configuration for index replication -->\n"
    '  <requestHandler name="/replication" class="solr.ReplicationHandler">\n',
    '    <lst name="follower">\n',
    f'      <str name="leaderUrl">http://{remote_host}:8983/solr/arclight</str>\n',
    '      <str name="pollInterval">00:00:20</str>\n',
    "    </lst>\n",
    "  </requestHandler>\n\n",
]

# insert leader/follower config
if os.environ.get("REPLICATION_ROLE") == "leader":
    solr_config[-1:-1] = leader_config
elif os.environ.get("REPLICATION_ROLE") == "follower":
    solr_config[-1:-1] = follower_config

with open(solrconfig_path, "w") as f:
    for line in solr_config:
        f.write(f"{line}")
