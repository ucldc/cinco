Rails.application.configure do
  # removes timestamp before json logs
  config.logger = ActiveSupport::Logger.new(STDOUT)

  config.lograge.enabled = true if Rails.env.production?

  config.lograge.custom_options = lambda do |event|
      {
        time: Time.now,
        query_string: event.payload[:query_string]
      }
  end

    config.lograge.formatter = Lograge::Formatters::Json.new
  end
