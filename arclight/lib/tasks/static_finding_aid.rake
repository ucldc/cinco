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
      # Create a proper request environment
      env = Rack::MockRequest.env_for("http://localhost:3000/findaid/static/#{id}")
      env["rack.session"] = {}
      env["rack.session.options"] = {}
      request = ActionDispatch::Request.new(env)
      response = ActionDispatch::Response.new

      # Set up the controller with proper context
      controller = StaticFindingAidController.new
      controller.set_request! request
      controller.set_response! response
      controller.params = ActionController::Parameters.new(id: id, controller: "static_finding_aid", action: "show")

      # Call the show action
      controller.process(:show)

      if response.status == 200
        puts "✓ Successfully generated static finding aid for #{id}"

        # Check if it was uploaded to S3
        if ENV["S3_BUCKET"].present?
          puts "✓ Content uploaded to S3 bucket: #{ENV['S3_BUCKET']}"
          puts "  Path: static_findaids/oac5/#{id}.html"
        else
          puts "⚠ S3_BUCKET not configured - content not uploaded to S3"
        end
      elsif response.status == 302
        puts "✗ Document not found in Solr - redirected to /findaid/#{id}"
        exit 1
      elsif response.status == 503
        puts "✗ Solr tree fetch timed out for #{id} - background render job queued"
        Kernel.exit!(1)
      else
        puts "✗ Failed with status: #{response.status}"
        exit 1
      end
    rescue => e
      puts "✗ Error generating static finding aid: #{e.message}"
      puts e.backtrace.first(5).join("\n")
      exit 1
    end
  end
end
