require "rails_helper"

RSpec.describe ApplicationHelper, type: :helper do
  describe "#repository_location_to_city" do
    it "returns the city and state extracted from location_html" do
        test_html = '<div class="al-repository-street-address-address1">901 E Tahquitz Canyon Way</div>
        <div class="al-repository-street-address-address2">Ste C-204</div>
        <div class="al-repository-street-address-city_state_zip_country">Palm Springs, CA 92262, US</div>'
        expect(helper.repository_location_to_city(test_html)).to eq("Palm Springs, CA")
    end
  end

    describe "#ark_rewrite_link_to" do
    let(:resource_class) { Struct.new(:label, :href) }
    let(:resource) { resource_class.new(ark_url, "https://#{ark_url}") }

    describe "when the link is to ark.cdlib.org" do
      let(:ark_url) { "ark.cdlib.org/ark:/13030/12345" }
      let(:expected_label) { "oac.cdlib.org/ark:/13030/12345" }
      let(:expected_href) { "https://oac.cdlib.org/ark:/13030/12345" }
      it "rewrites the link to  oac.cdlib.org" do
      expect(helper.ark_rewrite_link_to(resource))
        .to eql("<a href=\"#{expected_href}\">#{expected_label}</a>")
      end
    end
    describe "when the link is to not to ark.cdlib.org" do
      let(:ark_url) { "noac.cdlib.org/ark:/13030/12345" }
      let(:expected_label) { "noac.cdlib.org/ark:/13030/12345" }
      let(:expected_href) { "https://noac.cdlib.org/ark:/13030/12345" }
      it "leaves the link unchanged" do
      expect(helper.ark_rewrite_link_to(resource))
        .to eql("<a href=\"#{expected_href}\">#{expected_label}</a>")
      end
    end
  end
end
