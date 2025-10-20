# frozen_string_literal: true

# Middleware to capture CloudFront request ID and store it for use in Solr requests
class CloudfrontRequestIdMiddleware
    def initialize(app)
        @app = app
    end

    def call(env)
        request = Rack::Request.new(env)
        cloudfront_id = request.get_header("HTTP_X_AMZ_CF_ID")

        if cloudfront_id && defined?(RequestStore)
            RequestStore.store[:cloudfront_request_id] = cloudfront_id
        end

        @app.call(env)
    end
end

# Add the CloudFront request ID capture middleware to the Rails stack
Rails.application.config.middleware.use CloudfrontRequestIdMiddleware
