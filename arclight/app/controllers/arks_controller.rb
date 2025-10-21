class ArksController < ApplicationController
  # Keep this redirect here - rspec doesn't seem to like
  # external redirects in the routes file
  def calisphere
    respond_to do |format|
      format.any do
        # if the param is an ark, we want to match only the identifier portion
        # and throw out any extra path info after the ark id, arks should only
        # match ark:/\d{5}/[0-9a-zA-Z]+\/? - anything following the last slash
        # is extraneous. Note that ark:/ is part of the route.
        match = params[:id].match(/(^\d{5}\/[0-9a-zA-Z]+\/?)/)
        calisphere_id = match ? match[0] : params[:id]

        Rails.logger.info("Redirecting oac.cdlib.org/ark:/#{params[:id]} to calisphere.org/item/ark:/#{calisphere_id}")
        redirect_to(
          "https://calisphere.org/item/ark:/#{calisphere_id}",
          status: 301,
          allow_other_host: true
        )
      end
    end
  end
end
