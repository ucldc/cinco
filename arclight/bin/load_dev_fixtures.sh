if [ -z "${SOLR_URL}" ]; then
    echo $SOLR_URL
    echo "\$SOLR_URL must be set for this script to run"
    exit
fi

if [ -z "${FIXTURE_PATH}" ]; then
    FIXTURE_PATH="/app/fixtures"
fi

export REPOSITORY_ID=berkeley_bancroft
bundle exec traject -I lib/ -u $SOLR_URL -i xml -c lib/arclight/traject/ead2_config.rb $FIXTURE_PATH/xml/abart1_cubanc.xml -s eadid=abart1_cubanc.xml -s ark=ark:/13030/hb6d5nb8db
bundle exec traject -I lib/ -u $SOLR_URL -i xml -c lib/arclight/traject/ead2_config.rb $FIXTURE_PATH/xml/p2022_010_cubanc_as.xml -s eadid=p2022_010_cubanc_as.xml
bundle exec traject -I lib/ -u $SOLR_URL -i xml -c lib/arclight/traject/ead2_config.rb $FIXTURE_PATH/xml/pframed_cubanc.xml -s eadid=pframed_cubanc.xml
    # bundle exec traject -I lib/ -u $SOLR_URL -i xml -c lib/arclight/traject/ead2_config.rb $FIXTURE_PATH/xml/archivohistorico_film_cubanc.xml -s preview=true -s eadid=archivohistorico_film_cubanc.xml
bundle exec traject -I lib/ -u $SOLR_URL -i xml -c lib/arclight/traject/ead2_config.rb $FIXTURE_PATH/xml/banc-mss_p-g_282_ead.xml -s eadid=banc-mss_p-g_282_ead.xml
bundle exec traject -I lib/ -u $SOLR_URL -i xml -c lib/arclight/traject/ead2_config.rb $FIXTURE_PATH/xml/cu407_cuuarc.xml -s eadid=cu407_cuuarc.xml
bundle exec traject -I lib/ -u $SOLR_URL -i xml -c lib/arclight/traject/ead2_config.rb $FIXTURE_PATH/xml/p1905_16220_cubanc.xml -s eadid=p1905_16220_cubanc.xml
bundle exec traject -I lib/ -u $SOLR_URL -i xml -c lib/arclight/traject/ead2_config.rb $FIXTURE_PATH/xml/p2006_030_cubanc.xml -s eadid=p2006_030_cubanc.xml -s ark=ark:/13030/k6z326nw

export REPOSITORY_ID=uci_spcoll
bundle exec traject -I lib/ -u $SOLR_URL -i xml -c lib/arclight/traject/ead2_config.rb $FIXTURE_PATH/xml/f045.xml -s eadid=f045.xml
export REPOSITORY_ID=glhs
bundle exec traject -I lib/ -u $SOLR_URL -i xml -c lib/arclight/traject/ead2_config.rb $FIXTURE_PATH/xml/glbths_2017-18_GilbertBaker_FA.xml -s eadid=glbths_2017-18_GilbertBaker_FA.xml

curl $SOLR_URL/update?commit=true
