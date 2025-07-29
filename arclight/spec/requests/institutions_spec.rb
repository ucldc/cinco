require 'rails_helper'

RSpec.describe "Arclight::Repositories", type: :request do
  describe "GET institution landing page" do
     describe "by Arclight slug name" do
      it "returns http success" do
        get "/institutions/ampas_clac"
        expect(response).to have_http_status(:redirect)
        expect(response).to redirect_to(/\/search.*/)
      end
    end
    describe "by old OAC styles names with double colon divider" do
      it "returns http success" do
        get "/institutions/Academy+of+Motion+Picture+Arts+and+Sciences::Margaret+Herrick+Library"
        expect(response).to have_http_status(:redirect)
        expect(response).to redirect_to(/\/search.*/)
      end
    end
       describe "by old OAC styles names" do
      it "returns http success" do
        get "/institutions/Albany+Library"
        expect(response).to have_http_status(:redirect)
        expect(response).to redirect_to(/\/search.*/)
      end
    end
  end
  describe "Does not load pages for non existent institutions" do
      it "returns http not found response" do
        get "/institutions/NOT+REAL+Library"
        expect(response).to have_http_status(:redirect)
      end
    end
end
