class ArksController < ApplicationController
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
