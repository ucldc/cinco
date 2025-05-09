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
end
