Rails.application.configure do
  config.logger = ActiveSupport::Logger.new(STDOUT)

  config.lograge.enabled = true if Rails.env.production?

  config.lograge.custom_options = lambda do |event|
      request = event.payload[:request]
      {
        time: Time.now,
        query_string: request&.query_string,
        accept_header: request&.headers["Accept"],
        user_agent: request&.headers["User-Agent"],
        cloudfront_request_id: request&.headers["X-Amz-Cf-Id"],
        rails_request_id: request&.request_id,
        originally_requested_path: request&.original_fullpath
      }
  end

    config.lograge.formatter = Lograge::Formatters::Json.new
  end
