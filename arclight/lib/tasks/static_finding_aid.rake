namespace :static_finding_aid do
  desc "Generate static finding aid for a given Solr ID"
  task :generate, [ :id ] => :environment do |_t, args|
    unless args[:id].present?
      puts "Error: Please provide a Solr ID"
      puts "Usage: rake static_finding_aid:generate[<solr_id>]"
      exit 1
    end

    $stdout.sync = true

    id = args[:id]
    puts "Generating static finding aid for ID: #{id}"

    begin
      StaticFindingAidRenderJob.new.perform(id)

      if ENV["S3_BUCKET"].present?
        puts "✓ Successfully generated static finding aid for #{id}"
        puts "✓ Content uploaded to S3 bucket: #{ENV['S3_BUCKET']}"
        puts "  Path: static_findaids/oac5/#{id}.html"
      else
        puts "⚠ S3_BUCKET not configured - content not uploaded to S3"
      end
    rescue StaticFindingAidRenderJob::DocumentNotFound => e
      puts "✗ #{e.message}"
      exit 1
    rescue => e
      puts "✗ Error generating static finding aid: #{e.message}"
      puts e.backtrace.first(5).join("\n")
      exit 1
    end
  end
end
