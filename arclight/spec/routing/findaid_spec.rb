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
      controller: "arks",
      action: "findaid_static",
      ark: "ark:/13010/sdfsdfsf"
      )
  end

it "routes unescaped /findaid/ark:/*/entire_text/ to the static_finding_aid controller" do
    expect(get("/findaid/ark:/13010/sdfsdfsf/entire_text")).to route_to(
      controller: "arks",
      action: "findaid_static",
      ark: "ark:/13010/sdfsdfsf"
      )
  end

  it "routes admin after ark to the the findaid controller" do
    expect(get("/findaid/ark:/13010/sdfsdfsf/admin")).to route_to(
      controller: "arks",
      action: "findaid",
      ark: "ark:/13010/sdfsdfsf"
      )
  end

    it "routes admin/ after ark to the the findaid controller" do
    expect(get("/findaid/ark:/13010/sdfsdfsf/admin/")).to route_to(
      controller: "arks",
      action: "findaid",
      ark: "ark:/13010/sdfsdfsf"
      )
  end

    it "routes dsc after ark to the the findaid controller" do
    expect(get("/findaid/ark:/13010/sdfsdfsf/dsc")).to route_to(
      controller: "arks",
      action: "findaid",
      ark: "ark:/13010/sdfsdfsf"
      )
  end

    it "routes dsc/ after ark to the the findaid controller" do
    expect(get("/findaid/ark:/13010/sdfsdfsf/dsc/")).to route_to(
      controller: "arks",
      action: "findaid",
      ark: "ark:/13010/sdfsdfsf"
      )
  end

      it "routes dsc/ after ark to the the findaid controller" do
    expect(get("/findaid/ark:/13010/sdfsdfsf/dsc/?query=")).to route_to(
      controller: "arks",
      action: "findaid",
      ark: "ark:/13010/sdfsdfsf",
      query: ""
      )
  end

it "routes garbage after ark to the 404 controller" do
    expect(get("/findaid/ark:/13010/sdfsdfsf/garbage")).to route_to(
      controller: "errors",
      action: "not_found",
      ark: "ark:/13010/sdfsdfsf",
      else: "garbage"
      )
  end
end
