namespace :static_finding_aid do
  desc "Generate static finding aid for a given Solr ID"
  task :generate, [ :id ] => :environment do |_t, args|
    unless args[:id].present?
      puts "Error: Please provide a Solr ID"
      puts "Usage: rake static_finding_aid:generate[<solr_id>]"
      exit 1
    end

    id = args[:id]
    puts "Generating static finding aid for ID: #{id}"

    begin
      # Create a proper request environment
      env = Rack::MockRequest.env_for("http://localhost:3000/static_finding_aid/#{id}")
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
          puts "  Path: static_findaids/static_findaids/#{id}.html"
        else
          puts "⚠ S3_BUCKET not configured - content not uploaded to S3"
        end
      elsif response.status == 302
        puts "✗ Document not found in Solr - redirected to /findaid/#{id}"
        exit 1
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

  desc "Generate static finding aids for multiple Solr IDs from a file"
  task :generate_batch, [ :file_path ] => :environment do |_t, args|
    unless args[:file_path].present? && File.exist?(args[:file_path])
      puts "Error: Please provide a valid file path"
      puts "Usage: rake static_finding_aid:generate_batch[<path_to_file>]"
      puts "File should contain one Solr ID per line"
      exit 1
    end

    ids = File.readlines(args[:file_path]).map(&:strip).reject(&:empty?)
    total = ids.size
    success_count = 0
    failure_count = 0

    puts "Processing #{total} finding aids..."
    puts "=" * 50

    ids.each_with_index do |id, index|
      print "[#{index + 1}/#{total}] Processing #{id}... "

      begin
        env = Rack::MockRequest.env_for("http://localhost:3000/static_finding_aid/#{id}")
        env["rack.session"] = {}
        env["rack.session.options"] = {}
        request = ActionDispatch::Request.new(env)
        response = ActionDispatch::Response.new

        controller = StaticFindingAidController.new
        controller.set_request! request
        controller.set_response! response
        controller.params = ActionController::Parameters.new(id: id, controller: "static_finding_aid", action: "show")

        controller.process(:show)

        if response.status == 200
          puts "✓"
          success_count += 1
        else
          puts "✗ (status: #{response.status})"
          failure_count += 1
        end
      rescue => e
        puts "✗ (error: #{e.message})"
        failure_count += 1
      end
    end

    puts "=" * 50
    puts "Summary:"
    puts "  Total: #{total}"
    puts "  Success: #{success_count}"
    puts "  Failed: #{failure_count}"
  end
end
