# lib/tasks/repository.rake

namespace :repo do
  desc "Print the url-encoded name of an Arclight::Repository given REPOSITORY_ID (env var) or id argument"
  task :urlized_name, [ :id ] => :environment do |t, args|
    # Prefer argument, then fallback to ENV
    repo_id = args[:id] || ENV["REPOSITORY_ID"]

    if repo_id.nil? || repo_id.strip.empty?
      abort "Usage: rake repo:urlized_name[REPO_ID] or REPOSITORY_ID=REPO_ID rake repo:urlized_name"
    end

    repo = Arclight::Repository.find_by(slug: repo_id)

    if repo
      puts CGI.escape(repo.name)
    else
      abort "No repository found for id: #{repo_id}"
    end
  end
end
