require 'rails_helper'

RSpec.describe "OAC-4 /arks redirects to Calisphere", type: :request do
  describe "GET /ark:/13010/sdfsdfsf" do
    it "returns http redirect" do
      get "/ark:/13010/sdfsdfsf"
      expect(response).to have_http_status(:redirect)
      expect(response).to redirect_to("https://calisphere.org/item/ark:/13010/sdfsdfsf")
    end
  end
end
