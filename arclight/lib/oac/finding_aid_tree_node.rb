module Oac
  class FindingAidTreeNode
    attr_reader :document, :hierarchy_data

    def initialize(controller, id, has_children: true)
      @controller = controller
      @document = @controller.search_service.fetch(::RSolr.solr_escape(id))
      results = @controller.search_service.search_results do |builder|
        builder.blacklight_params[:id] = id
        builder
      end
      @hierarchy_data =  results.response["docs"].map { |doc| SolrDocument.new(doc) } if has_children || []
    end

    def children
      Rails.cache.fetch("#{@document.id}/children") do
        _get_children
      end
    end

    def _get_children
       @children ||= @hierarchy_data.map do  |doc|
          FindingAidTreeNode.new(
            @controller,
            doc.id,
            has_children: doc.fetch("child_component_count_isi", 0) > 0
          )
        end
    end

    def marshal_dump
      {}.tap do |result|
        result[:document] = @document.to_json
        result[:hierarchy_data] = @hierarchy_data.map { |d| d.to_json }
      end
    end

    def marshal_load(serialized_tree)
      @document = SolrDocument.new(JSON.parse(serialized_tree[:document]))
      @hierarchy_data = serialized_tree[:hierarchy_data].map { |d|  SolrDocument.new(JSON.parse(d)) }
    end
  end
end
