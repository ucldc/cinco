module Oac
  class FindingAidTreeNode
    attr_reader :document, :hierarchy_data

    def initialize(controller, id, has_children: true)
      @controller = controller
      @document = controller.search_service.fetch(::RSolr.solr_escape(id))
      default_solr_params = @controller.blacklight_config.default_solr_params.dup
      @controller.blacklight_config.default_solr_params.merge!(
        { fq: "_nest_parent_:#{::RSolr.solr_escape(id)}", sort: "sort_isi asc", facet: false }
      )
      @hierarchy_data = @controller.search_service.search_results.response["docs"].map { |doc| SolrDocument.new(doc) } if has_children || []
      @controller.blacklight_config.default_solr_params = default_solr_params
      children
    end

    def children
      @children ||= @hierarchy_data.map do  |doc|
        FindingAidTreeNode.new(
          @controller,
          doc.id,
          has_children: doc.fetch("child_component_count_isi", 0) > 0
        )
      end
    end
  end
end
