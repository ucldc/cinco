# README

* Ruby version

ruby 3.2
rails 7.2

* System dependencies

* Configuration

* Database creation

* Database initialization

* How to run the test suite

* Services (job queues, cache servers, search engines, etc.)

* Deployment instructions

* Indexing

To run the indexer with our customizations use the following command from the arclight root:

```
bundle exec traject -I lib/ -u http://<solr_url>:8983/solr/blacklight-core -i xml -c lib/arclight/traject/ead2_config.rb path/to/file.xml
```

In order to add a finding aid to a specific repository set the environment variable `REPOSITORY_ID` to Repository.code set in cincoctrl

By default the indexer will look for a file called `extracted-supplementary-files-text.txt` in the same directory as the given finding aid.  If you want to change this default name you can set the environment variable `TEXT_FILE_NAME`. You can also set the directory for the text file by setting `TEXT_FILE_DIR`.