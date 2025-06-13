#!/usr/bin/env bash
set -e

pwd
rm -f /app/tmp/pids/server.pid
bundle exec rails server -b 0.0.0.0 -p 3000
bundle install
bundle exec rails engine_cart:generate
bundle exec rails arclight:seed
bundle exec rake arclight:server["-p 3000 -b 0.0.0.0"]
