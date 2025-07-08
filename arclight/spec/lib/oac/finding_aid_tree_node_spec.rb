require 'rails_helper'
require 'oac/finding_aid_tree_node'

RSpec.describe Oac::FindingAidTreeNode do
  let(:tree) { described_class.new(controller, id) }
  let(:controller) { instance_double(StaticFindingAidController) }
  let(:id) { 'test_id' }
  let(:first_hierarchy_response) {
    ActiveSupport::HashWithIndifferentAccess.new(
      { "docs": [ { id: "1a" }, { id: "2a" }, { id: "3a" } ] })
  }
  let(:second_hierarchy_response) {
    ActiveSupport::HashWithIndifferentAccess.new(
      { "docs": [ { id: "4a" }, { id: "5a" }, { id: "6a" } ] }
    )
  }
  let(:empty_hierarchy_response) {
    ActiveSupport::HashWithIndifferentAccess.new(
      { "docs": [] }
    )
  }

  let(:default_solr_params) {
    { default: "params" }
  }

  before do
    allow(controller).to receive(:search_service)
    allow(controller.search_service).to receive(:fetch)
    allow(controller.search_service).to receive(:search_results)
    allow(controller.search_service.search_results).to receive(:response).and_return(
      first_hierarchy_response,
      second_hierarchy_response,
      empty_hierarchy_response
    )

    allow(controller).to receive(:blacklight_config)

    allow(controller.blacklight_config).to receive(:default_solr_params).and_return(default_solr_params)
    allow(controller.blacklight_config).to receive(:default_solr_params=)
    allow(controller.blacklight_config.default_solr_params).to receive(:merge!)
  end

  describe "creating an instance" do
    before { tree }
    it "calls the controller's search service fetch method" do
      expect(controller.search_service).to have_received(:fetch).with(id)
    end
    it "temporarily merge's some default_solr_params" do
      expect(controller.blacklight_config.default_solr_params).to have_received(:merge!).with({ fq: "_nest_parent_:#{id}", sort: "sort_isi asc", facet: false })
    end
    it "leaves the default_solr_params in their original state" do
      expect(controller.blacklight_config).to have_received(:default_solr_params=).with(default_solr_params).at_least(:once)
    end
  end
  describe "children method" do
    before { tree }
    it "returns an array of #{described_class.name} objects" do
      expect(tree.children.map { |c| c.class }.uniq).to be_eql([ described_class ])
    end
    it "nests children" do
      expect(tree.children.first.children.first).to be_a(described_class)
    end
  end
end
