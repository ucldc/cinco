require "rails_helper"
RSpec.describe "routes for findaid", type: :routing do
  it "routes unescaped /findaid/ark:/* to the catalog controller" do
    expect(get("/findaid/ark:/13010/sdfsdfsf")).to route_to(
      controller: "catalog",
      action: "show",
      id: "ark:/13010/sdfsdfsf"
      )
  end

  it "routes non-ark /findaid/* to the catalog controller" do
    expect(get("/findaid/sdfsdfsf")).to route_to(
      controller: "catalog",
      action: "show",
      id: "sdfsdfsf"
      )
  end

  it "routes garbage after ark to the 404 controller" do
    expect(get("/findaid/ark:/13010/sdfsdfsf/garbage")).to route_to(
      controller: "errors",
      action: "not_found",
      id: "ark:/13010/sdfsdfsf",
      else: "garbage"
      )
  end
end
