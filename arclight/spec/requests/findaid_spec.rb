# Test redirects as request specs, not routing specs
# https://stackoverflow.com/questions/10842448/do-routing-specs-support-redirect-routes-rspec

require 'rails_helper'

RSpec.describe "OAC-4 style findaid redirects", type: :request do
  describe "GET /findaid/ark:/13010/sdfsdfsf/entire_text" do
    it "returns http redirect" do
      get "/findaid/ark:/13010/sdfsdfsf/entire_text"
      expect(response).to have_http_status(:redirect)
      expect(response).to redirect_to("/findaid/static/ark:/13010/sdfsdfsf")
    end
  end

  describe "GET /findaid/ark:/13010/sdfsdfsf/entire_text/" do
    it "returns http redirect" do
      get "/findaid/ark:/13010/sdfsdfsf/entire_text/"
      expect(response).to have_http_status(:redirect)
      expect(response).to redirect_to("/findaid/static/ark:/13010/sdfsdfsf")
    end
  end

  describe "GET /findaid/sdfsdfsf/entire_text" do
    it "returns http redirect for non-ark finding aids" do
      get "/findaid/sdfsdfsf/entire_text"
      expect(response).to have_http_status(:redirect)
      expect(response).to redirect_to("/findaid/static/sdfsdfsf")
    end
  end

  describe "GET /findaid/ark:/13010/sdfsdfsf/admin" do
    it "returns http redirect" do
      get "/findaid/ark:/13010/sdfsdfsf/admin"
      expect(response).to have_http_status(:redirect)
      expect(response).to redirect_to("/findaid/ark:/13010/sdfsdfsf")
    end
  end

  describe "GET /findaid/ark:/13010/sdfsdfsf/admin/" do
    it "returns http redirect" do
      get "/findaid/ark:/13010/sdfsdfsf/admin/"
      expect(response).to have_http_status(:redirect)
      expect(response).to redirect_to("/findaid/ark:/13010/sdfsdfsf")
    end
  end

  describe "GET /findaid/sdfsdfsf/admin" do
    it "returns http redirect for non-ark finding aids" do
      get "/findaid/sdfsdfsf/admin"
      expect(response).to have_http_status(:redirect)
      expect(response).to redirect_to("/findaid/sdfsdfsf")
    end
  end

  describe "GET /findaid/ark:/13010/sdfsdfsf/dsc" do
    it "returns http redirect" do
      get "/findaid/ark:/13010/sdfsdfsf/dsc"
      expect(response).to have_http_status(:redirect)
      expect(response).to redirect_to("/findaid/ark:/13010/sdfsdfsf")
    end
  end

  describe "GET /findaid/ark:/13010/sdfsdfsf/dsc/" do
    it "returns http redirect" do
      get "/findaid/ark:/13010/sdfsdfsf/dsc/"
      expect(response).to have_http_status(:redirect)
      expect(response).to redirect_to("/findaid/ark:/13010/sdfsdfsf")
    end
  end

  describe "GET /findaid/ark:/13010/sdfsdfsf/dsc/?query=" do
    it "returns http redirect" do
      get "/findaid/ark:/13010/sdfsdfsf/dsc/?query="
      expect(response).to have_http_status(:redirect)
      expect(response).to redirect_to("/findaid/ark:/13010/sdfsdfsf")
    end
  end

  describe "GET /findaid/sdfsdfsf/dsc" do
    it "returns http redirect for non-ark finding aids" do
      get "/findaid/sdfsdfsf/dsc"
      expect(response).to have_http_status(:redirect)
      expect(response).to redirect_to("/findaid/sdfsdfsf")
    end
  end

  describe "GET /findaid/ark:/13010/sdfsdfsf/garbage" do
    it "returns http not found" do
      get "/findaid/ark:/13010/sdfsdfsf/garbage"
      expect(response).to have_http_status(:not_found)
    end
  end

  describe "GET /findaid/sdfsdfsf/garbage" do
    it "returns http not found" do
      get "/findaid/sdfsdfsf/garbage"
      expect(response).to have_http_status(:not_found)
    end
  end
end
