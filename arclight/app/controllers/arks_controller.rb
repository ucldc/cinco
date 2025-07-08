class ArksController < ApplicationController
  def findaid
    redirect_to solr_document_url(params[:ark].to_param)
  end
end
