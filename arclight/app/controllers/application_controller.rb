class ApplicationController < ActionController::Base
  # Adds a few additional behaviors into the application controller
  include Blacklight::Controller
  include Blacklight::LocalePicker::Concern
  layout :determine_layout if respond_to? :layout

  # Only allow modern browsers supporting webp images, web push, badges, import maps, CSS nesting, and CSS :has.
  allow_browser versions: :modern

  helper_method :solr_document_path

  def solr_document_path(*args, **options)
    Rails.logger.info("solr_document_path called with args: #{args}, options: #{options}")
    document_id = options[:id] || (args.first.respond_to?(:id) ? args.first.id : args.first)
    encoded_path = super(*args, **options)
    Rails.logger.info("Generated path from original: #{encoded_path}")

    if document_id.to_s.start_with?("ark:")
      Rails.logger.info("ARK detected, generating custom solr document path.")
      encoded_path.gsub!("%2F", "/")
      Rails.logger.info("Rewritten solr document path: #{encoded_path}")
    end
    encoded_path
  end
end
