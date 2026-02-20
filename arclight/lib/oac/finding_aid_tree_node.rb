module Oac
  class FindingAidTreeNode
    attr_reader :document

    def initialize(controller, id, doc_hash: nil)
      @controller = controller
      @doc_hash = doc_hash

      if doc_hash.nil?
        # Fetch the entire tree in a single query
        repository = Blacklight.repository_class.new(@controller.blacklight_config)
        response = repository.search(
          q: "id:#{RSolr.solr_escape(id)}",
          fl: "*,[child]",
          rows: 1
        )
        @doc_hash = response["response"]["docs"].first
      end

      @document = SolrDocument.new(@doc_hash) if @doc_hash
    end

    def children
      @children ||= begin
        child_docs = @doc_hash["components"] || []
        child_docs.map { |child_hash| FindingAidTreeNode.new(@controller, nil, doc_hash: child_hash) }
      end
    end
  end
end
