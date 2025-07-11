module Oac
  class FindingAidTreeNode
    attr_reader :document, :hierarchy_data

    def initialize(controller, id, has_children: true)
      @controller = controller
      @document = controller.search_service.fetch(::RSolr.solr_escape(id))
      results = @controller.search_service.search_results do |builder|
        builder.blacklight_params[:id] = id
        builder
      end
      @hierarchy_data =  results.response["docs"].map { |doc| SolrDocument.new(doc) } if has_children || []
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
