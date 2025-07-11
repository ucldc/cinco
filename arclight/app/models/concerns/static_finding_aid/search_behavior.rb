# frozen_string_literal: true

# Overridden from Arclight and OAC in order to escape IDs
# and add the hierachy behavior to all searches

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

    # rubocop:disable Metrics/AbcSize, Metrics/CyclomaticComplexity
    def add_hierarchy_behavior(solr_parameters)
      solr_parameters[:fq] ||= []
      # Escape IDs because arks contain special characters
      solr_parameters[:fq] << "_nest_parent_:#{RSolr.solr_escape(blacklight_params[:id])}"
      solr_parameters[:rows] = blacklight_params[:per_page]&.to_i || blacklight_params[:limit]&.to_i || 999_999_999
      solr_parameters[:start] = blacklight_params[:offset] if blacklight_params[:offset]
      solr_parameters[:sort] = "sort_isi asc"
      solr_parameters[:facet] = false
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
