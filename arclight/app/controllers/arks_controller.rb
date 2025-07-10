class ArksController < ApplicationController
  def findaid
    redirect_to solr_document_url(params[:ark].to_param)
  end

  def findaid_static
    redirect_to static_finding_aid_url(params[:ark].to_param)
  end
end
