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
