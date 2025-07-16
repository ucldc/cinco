require "net/http"

namespace :cache do
  desc "Clear cache for Static Guide by id"
  task :clear_for, [ :id ] => :environment do |_t, args|
    select_sql = "SELECT key from solid_cache_entries where key like '%#{args[:id]}%'"
    delete_sql = "DELETE from solid_cache_entries where key like '%#{args[:id]}%'"
    puts "Number of records before clearance:"
    puts ActiveRecord::Base.connection.execute(select_sql).size
    ActiveRecord::Base.connection.execute(delete_sql)
    puts "Number of records after delete:"
    puts ActiveRecord::Base.connection.execute(select_sql).size
  end

  desc "Generate cache entry for Static Guide by id"
  task :generate_for, [ :id ] => :environment do |_t, args|
    path = Rails.application.routes.url_helpers.static_finding_aid_path(id: args[:id])
    Net::HTTP.get(URI.parse("http://127.0.0.1:3000#{path}"))
  end
end
