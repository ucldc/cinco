require "rails_helper"

RSpec.describe StaticFindingAidController, type: :controller do
  describe "#cache_is_valid?" do
    subject(:controller) { described_class.new }

    let(:document) do
      SolrDocument.new(
        "_version_"                => "12345",
        "total_component_count_is" => "42",
        "timestamp"                => "2026-02-20T00:00:00Z"
      )
    end

    let(:matching_metadata) do
      {
        "version"               => "12345",
        "total-component-count" => "42",
        "timestamp"             => "2026-02-20T00:00:00Z"
      }
    end

    it "returns true when all metadata fields match the document" do
      expect(controller.send(:cache_is_valid?, matching_metadata, document)).to be true
    end

    it "returns false when version does not match" do
      metadata = matching_metadata.merge("version" => "99999")
      expect(controller.send(:cache_is_valid?, metadata, document)).to be false
    end

    it "returns false when component count does not match" do
      metadata = matching_metadata.merge("total-component-count" => "0")
      expect(controller.send(:cache_is_valid?, metadata, document)).to be false
    end

    it "returns false when timestamp does not match" do
      metadata = matching_metadata.merge("timestamp" => "1999-01-01T00:00:00Z")
      expect(controller.send(:cache_is_valid?, metadata, document)).to be false
    end

    it "returns false when metadata is empty" do
      expect(controller.send(:cache_is_valid?, {}, document)).to be false
    end

    it "returns false when version is missing" do
      metadata = matching_metadata.except("version")
      expect(controller.send(:cache_is_valid?, metadata, document)).to be false
    end

    it "returns false when total-component-count is missing" do
      metadata = matching_metadata.except("total-component-count")
      expect(controller.send(:cache_is_valid?, metadata, document)).to be false
    end

    it "returns false when timestamp is missing" do
      metadata = matching_metadata.except("timestamp")
      expect(controller.send(:cache_is_valid?, metadata, document)).to be false
    end
  end
end
