module StaticFindingAid
  module S3Cache
    # Returns the S3 object body if the path exists and the optional cache_check_fn passes,
    # nil otherwise.
    def fetch_from_s3(path, cache_check_fn = nil, document: nil)
      s3_bucket = ENV["S3_BUCKET"]
      return nil unless s3_bucket.present?

      s3 = Aws::S3::Resource.new
      obj = s3.bucket(s3_bucket).object("static_findaids/#{path}")
      head = obj.head

      if cache_check_fn.respond_to?(:call)
        if cache_check_fn.call(head.metadata, document)
          Rails.logger.info("S3 cache valid for #{path}, serving cached content")
          obj.get.body.read
        else
          Rails.logger.info("S3 cache invalid for #{path}")
          nil
        end
      else
        Rails.logger.info("S3 cache assumed valid for #{path}, serving cached content")
        obj.get.body.read
      end
    rescue Aws::S3::Errors::NotFound
      Rails.logger.info("No S3 file found at #{path}")
      nil
    rescue => e
      Rails.logger.warn("S3 request failed for #{path}: #{e.message}")
      nil
    end

    # Returns true if the S3 object at oac5/<id>.html has metadata matching the document.
    def s3_cache_current?(id, document)
      s3_bucket = ENV["S3_BUCKET"]
      return false unless s3_bucket.present?

      s3 = Aws::S3::Resource.new
      obj = s3.bucket(s3_bucket).object("static_findaids/oac5/#{id}.html")
      cache_is_valid?(obj.head.metadata, document)
    rescue Aws::S3::Errors::NotFound
      false
    rescue => e
      Rails.logger.warn("S3 head check failed for #{id}: #{e.message}")
      false
    end


    def cache_is_valid?(s3_metadata, document)
      # Check if S3 metadata matches current Solr document
      # todo: this log output is conservative and verbose - remove at some point
      s3_version = s3_metadata["version"]
      s3_component_count = s3_metadata["total-component-count"]
      s3_timestamp = s3_metadata["timestamp"]
      Rails.logger.info("S3  metadata - version: #{s3_version}, component_count: #{s3_component_count}, timestamp: #{s3_timestamp}")

      doc_version = document["_version_"].to_s
      doc_component_count = document["total_component_count_is"].to_s
      doc_timestamp = document["timestamp"].to_s
      Rails.logger.info("Doc metadata - version: #{doc_version}, component_count: #{doc_component_count}, timestamp: #{doc_timestamp}")

      return false unless s3_version && s3_component_count && s3_timestamp

      s3_time = DateTime.iso8601(s3_timestamp)
      doc_time = DateTime.iso8601(doc_timestamp)

      (s3_version == doc_version &&
        s3_component_count == doc_component_count &&
        s3_time == doc_time) or
        (s3_component_count == doc_component_count &&
        s3_time >= doc_time)
    rescue ArgumentError
      false
    end


    def upload_to_s3(id, html_content, document)
      s3_bucket = ENV["S3_BUCKET"]
      return unless s3_bucket.present?

      s3 = Aws::S3::Resource.new
      bucket = s3.bucket(s3_bucket)

      Rails.logger.info("Uploading static finding aid partial for #{id} to S3")
      bucket.object("static_findaids/oac5/#{id}.html").put(
        body: html_content,
        content_type: "text/html",
        metadata: {
          "version" => document["_version_"].to_s,
          "total-component-count" => document["total_component_count_is"].to_s,
          "timestamp" => document["timestamp"].to_s
        }
      )
    end
  end
end
