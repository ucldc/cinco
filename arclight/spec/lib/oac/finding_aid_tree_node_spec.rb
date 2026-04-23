require 'rails_helper'
require 'oac/finding_aid_tree_node'

RSpec.describe Oac::FindingAidTreeNode do
  let(:id) { 'test_id' }
  let(:doc_hash) do
    {
      "id" => id,
      "_version_" => "1234",
      "components" => [
        { "id" => "child_1", "components" => [ { "id" => "grandchild_1", "components" => [] } ] },
        { "id" => "child_2", "components" => [] }
      ]
    }
  end
  let(:solr_connection) { instance_double(RSolr::Client) }

  before do
    allow(Blacklight.default_index).to receive(:connection).and_return(solr_connection)
    allow(solr_connection).to receive(:send_and_receive).with("get", params: { id: id, fl: "*,[child]" })
                                                        .and_return({ "doc" => doc_hash })
  end

  describe "creating an instance" do
    it "fetches the document via RTG" do
      described_class.new(id)
      expect(solr_connection).to have_received(:send_and_receive).with("get", params: { id: id, fl: "*,[child]" })
    end

    it "exposes the SolrDocument" do
      tree = described_class.new(id)
      expect(tree.document).to be_a(SolrDocument)
      expect(tree.document["id"]).to eq(id)
    end

    context "when the document is not found" do
      before do
        allow(solr_connection).to receive(:send_and_receive).and_return({ "doc" => nil })
      end

      it "sets document to nil" do
        tree = described_class.new(id)
        expect(tree.document).to be_nil
      end
    end
  end

  describe "#children" do
    let(:tree) { described_class.new(id) }

    it "returns an array of #{described_class.name} objects" do
      expect(tree.children.map(&:class).uniq).to eq([ described_class ])
    end

    it "nests children" do
      expect(tree.children.first.children.first).to be_a(described_class)
    end

    it "returns the correct number of top-level children" do
      expect(tree.children.length).to eq(2)
    end
  end

  describe "constructing from a doc_hash directly" do
    it "does not call Solr" do
      described_class.new(nil, doc_hash: doc_hash)
      expect(solr_connection).not_to have_received(:send_and_receive)
    end
  end
end
