class ApplicationController < ActionController::Base
  # Adds a few additional behaviors into the application controller
  include Blacklight::Controller
  include Blacklight::LocalePicker::Concern
  layout :determine_layout if respond_to? :layout

  # Only allow modern browsers supporting webp images, web push, badges, import maps, CSS nesting, and CSS :has.
  allow_browser versions: :modern

  # temporarily log accept headers and rails-determined formats
  # to debug 406 errors TODO: remove after debugging
  before_action :log_accept_and_format

  private
  def log_accept_and_format
    Rails.logger.info({
      accept: request.headers["Accept"],
      requested_format: request.format&.to_s,
      params_format: params[:format],
      path: request.fullpath
    }.to_json)
  end
end
