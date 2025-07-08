require "rails_helper"
RSpec.describe "routes for findaid", type: :routing do
 it "routes unescaped /findaid/ark:/* to the catalog controller" do
    expect(get("/findaid/ark:/13010/sdfsdfsf")).to route_to(
      controller: "arks",
      action: "findaid",
      ark: "ark:/13010/sdfsdfsf"
      )
  end
it "routes escaped /findaid/ark:/* to the catalog controller" do
    expect(get("/findaid/ark:%2F13010%2Fsdfsdfsf")).to route_to(
      controller: "catalog",
      action: "show",
      id: "ark:/13010/sdfsdfsf"
      )
  end

it "routes escaped /findaid/ark:/*/entire_text/ to the static_finding_aid controller" do
    expect(get("/findaid/ark:%2F13010%2Fsdfsdfsf/entire_text")).to route_to(
      controller: "static_finding_aid",
      action: "show",
      id: "ark:/13010/sdfsdfsf"
      )
  end

it "routes unescaped /findaid/ark:/*/entire_text/ to the static_finding_aid controller" do
    expect(get("/findaid/ark:/13010/sdfsdfsf/entire_text")).to route_to(
      controller: "static_finding_aid",
      action: "show",
      id: "ark:/13010/sdfsdfsf"
      )
  end
end
