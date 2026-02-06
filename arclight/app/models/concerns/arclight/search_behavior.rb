# frozen_string_literal: true

## Overridden from Arclight in order to escape IDs

require "rsolr"

module Arclight
  ##
  # Customized Search Behavior for Arclight
  module SearchBehavior
    extend ActiveSupport::Concern

    included do
      self.default_processor_chain += %i[
        add_highlighting
        add_grouping
        add_hierarchy_behavior
      ]
    end

    # rubocop:disable Metrics/AbcSize, Metrics/CyclomaticComplexity
    def add_hierarchy_behavior(solr_parameters)
      return unless search_state.controller&.action_name == "hierarchy"

      solr_parameters[:fq] ||= []
      # Escape IDs because arks contain special characters
      solr_parameters[:fq] << "_nest_parent_:#{RSolr.solr_escape(blacklight_params[:id])}"
      solr_parameters[:rows] = blacklight_params[:per_page]&.to_i || blacklight_params[:limit]&.to_i || 999_999_999
      solr_parameters[:start] = blacklight_params[:offset] if blacklight_params[:offset]
      solr_parameters[:sort] = "sort_isi asc"
      solr_parameters[:facet] = false
      # Optimize performance by only fetching fields needed for hierarchy display
      solr_parameters[:fl] = [
        "id",
        "title_ssm",
        "normalized_title_ssm",
        "level_ssm",
        "sort_isi",
        "ref_ssi",
        "unitid_ssm",
        "containers_ssim",
        "extent_ssm",
        "unitdate_ssm",
        "normalized_date_ssm",
        "child_component_count_isi",
        "_nest_path_"
      ].join(",")
    end
    # rubocop:enable Metrics/AbcSize, Metrics/CyclomaticComplexity

    ##
    # Add highlighting
    def add_highlighting(solr_params)
      solr_params["hl"] = true
      solr_params["hl.fl"] = CatalogController.blacklight_config.highlight_field
      solr_params["hl.snippets"] = 3
      solr_params
    end

    ##
    # Adds grouping parameters for Solr if enabled
    def add_grouping(solr_params)
      solr_params.merge!(Arclight::Engine.config.catalog_controller_group_query_params) if blacklight_params[:group] == "true"

      solr_params
    end
  end
end
