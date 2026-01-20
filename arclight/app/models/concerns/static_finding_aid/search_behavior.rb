# frozen_string_literal: true

# Overridden from Arclight and OAC to fetch entire document tree
# with nested children in a single query

require "rsolr"

module StaticFindingAid
  ##
  # Customized Search Behavior for Arclight
  module SearchBehavior
    extend ActiveSupport::Concern

    included do
      self.default_processor_chain += %i[
        add_hierarchy_behavior
      ]
    end

    # rubocop:disable Metrics/AbcSize
    def add_hierarchy_behavior(solr_parameters)
      return unless blacklight_params[:id]

      # Fetch the document by ID with all nested children in a single query
      solr_parameters[:fq] ||= []
      solr_parameters[:fq] << "id:#{RSolr.solr_escape(blacklight_params[:id])}"
      solr_parameters[:fl] = "*,-text,[child fl=\"*,-text\"]"
      solr_parameters[:rows] = 1
      solr_parameters[:facet] = false

      # Clean up any facet parameters
      solr_parameters.delete("facet.query")
      solr_parameters.delete("facet.field")
      solr_parameters.delete("f.repository_ssim.facet.limit")
      solr_parameters.delete("f.collection_ssim.facet.limit")
      solr_parameters.delete("f.creator_ssim.facet.limit")
      solr_parameters.delete("f.names_ssim.facet.limit")
      solr_parameters.delete("f.geogname_ssim.facet.limit")
      solr_parameters.delete("f.access_subjects_ssim.facet.limit")
      solr_parameters.delete("f.level_ssim.facet.limit")
    end
    # rubocop:enable Metrics/AbcSize, Metrics/CyclomaticComplexity
  end
end
