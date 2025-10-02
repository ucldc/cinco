require "rails_helper"
RSpec.describe "routes for static findaid", type: :routing do
  it "routes unescaped /findaid/static/ark:/* to the static findaid controller" do
    expect(get("/findaid/static/ark:/13010/sdfsdfsf")).to route_to(
      controller: "static_finding_aid",
      action: "show",
      id: "ark:/13010/sdfsdfsf"
      )
  end

  it "routes non-ark /findaid/static/* to the static findaid controller" do
    expect(get("/findaid/static/sdfsdfsf")).to route_to(
      controller: "static_finding_aid",
      action: "show",
      id: "sdfsdfsf"
      )
  end
end
