class ArksController < ApplicationController
  def findaid
    redirect_to solr_document_url(params[:ark].to_param)
  end

  def findaid_static
    redirect_to static_finding_aid_url(params[:ark].to_param)
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
