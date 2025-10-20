# frozen_string_literal: true

# RSolr Documentation: https://github.com/rsolr/rsolr/tree/v2.6.0
# Faraday Middleware Documentation: https://lostisland.github.io/faraday/#/middleware/index
# X-Trace-Id Header Documentation: https://solr.apache.org/guide/solr/latest/deployment-guide/distributed-tracing.html

# Middleware to add CloudFront request ID as X-Trace-Id header to Solr requests
class SolrTracingMiddleware < Faraday::Middleware
    def call(env)
        # Get CloudFront ID from RequestStore if available
        cloudfront_id = RequestStore.store[:cloudfront_request_id] if defined?(RequestStore)

        if cloudfront_id
            env.request_headers["X-Trace-Id"] = cloudfront_id
            Rails.logger.debug "Added X-Trace-Id: #{cloudfront_id} to Solr request: #{env.url}"
        end

        @app.call(env)
    end
end

# Configure RSolr to use our middleware
if defined?(RSolr)
    Rails.application.config.after_initialize do
        if defined?(Blacklight::Solr::Repository)
            # Override the Blacklight Solr repository's build_connection method
            Blacklight::Solr::Repository.class_eval do
                private

                def build_connection
                    conn_config = connection_config.merge(adapter: connection_config[:http_adapter])

                    # Ensure we have an adapter for Faraday middleware
                    conn_config[:adapter] ||= :net_http

                    # Create RSolr connection
                    connection = RSolr.connect(conn_config)

                    # Add our tracing middleware to the Faraday connection
                    if connection.respond_to?(:connection) && connection.connection.respond_to?(:builder)
                        connection.connection.builder.insert(0, SolrTracingMiddleware)
                    end

                    connection
                end
            end
        end
    end
end
