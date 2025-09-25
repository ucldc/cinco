class ArksController < ApplicationController
  def findaid
    # log the URL we are redirecting to
    url = solr_document_url(params[:ark].to_param)
    Rails.logger.info({
      event: "Redirecting to Solr Document URL",
      solr_document_url: url,
      rails_request_id: request.uuid,
      format: request.format.symbol,
      path: request.path,
      controller: self.class.name,
      action: action_name,
      cloudfront_request_id: request.headers["X-Amz-Cf-Id"],
      accept_header: request.headers["Accept"],
      user_agent: request.headers["User-Agent"]
    }.to_json)
    redirect_to url
  end

  def findaid_static
    # log the URL we are redirecting to
    url = static_finding_aid_url(params[:ark].to_param)
    Rails.logger.info({
      event: "Redirecting to Static Finding Aid URL",
      static_finding_aid_url: url,
      rails_request_id: request.uuid,
      format: request.format.symbol,
      path: request.path,
      controller: self.class.name,
      action: action_name,
      cloudfront_request_id: request.headers["X-Amz-Cf-Id"],
      accept_header: request.headers["Accept"],
      user_agent: request.headers["User-Agent"]
    }.to_json)
    redirect_to url
  end

  def calisphere
    respond_to do |format|
      format.any do
        redirect_to(
          "https://calisphere.org/item/ark:/#{params[:id]}",
          status: 301,
          allow_other_host: true
        )
      end
    end
  end
end
