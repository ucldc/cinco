
namespace :cache do
  desc "Clear cache for Static Guide by id"
  task :clear_for, [ :id ] => :environment do |_t, args|
    puts "deleting #{args[:id]}/children"
    puts Rails.cache.delete("#{args[:id]}/children")
  end

  desc "Generate cache entry for Static Guide by id"
  task :generate_for, [ :id ] => :environment do |_t, args|
    path = Rails.application.routes.url_helpers.static_finding_aid_path(id: args[:id])
    Net::HTTP.get(URI.parse("http://127.0.0.1:3000#{path}"))
  end
end
