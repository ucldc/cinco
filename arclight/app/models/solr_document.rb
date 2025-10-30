# frozen_string_literal: true

# Represents a single document returned from Solr
class SolrDocument
  include Blacklight::Solr::Document
  include Arclight::SolrDocument

  def to_param
    # For ARK identifiers, return the raw ID without encoding
    # Rails routing should handle ARK identifiers as special path segments
    # this does not work as it should, instead see:
    #   - app/helpers/application_helper.rb hierarchy_solr_document_path
    #   - app/helpers/application_helper.rb static_finding_aid_path
    #   - app/helpers/application_helper.rb solr_document_path
    Rails.logger.info("SolrDocument to_param called for ID: #{self.id}")
    if self.id.to_s.start_with?("ark:")
      self.id.to_s
    else
      super
    end
  end

  # self.unique_key = 'id'

  # DublinCore uses the semantic field mappings below to assemble an OAI-compliant Dublin Core document
  # Semantic mappings of solr stored fields. Fields may be multi or
  # single valued. See Blacklight::Document::SemanticFields#field_semantics
  # and Blacklight::Document::SemanticFields#to_semantic_values
  # Recommendation: Use field names from Dublin Core
  use_extension(Blacklight::Document::DublinCore)

  # Add title_filing and unittitle attributes to SolrDocument
  attribute :title_filing, :string, "title_filing_ssi"
  attribute :unittitle, :string, "unittitle_ssm"

  # Override blacklight behavior to return title_filing if available,
  # with unittitle and id as fallbacks.
  def collection_name
    if collection&.title_filing
      collection&.title_filing
    elsif collection&.unittitle
      collection&.unittitle
    else
      collection&.id
    end
  end
end
