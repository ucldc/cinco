module Oac
  class FindingAidTreeNode
    attr_reader :document

    def initialize(id, doc_hash: nil)
      @doc_hash = doc_hash

      if doc_hash.nil?
        # Fetch the entire tree in a single query using /get (Real-Time Get).
        # Uses Blacklight.default_index.connection (memoized RSolr client built
        # from blacklight.yml) so no controller reference is needed.
        response = Blacklight.default_index.connection.send_and_receive(
          "get",
          params: { id: id, fl: "*,[child]" }
        )
        @doc_hash = response["doc"]
      end

      @document = SolrDocument.new(@doc_hash) if @doc_hash
    end

    def children
      @children ||= begin
        child_docs = @doc_hash["components"] || []
        child_docs.map { |child_hash| FindingAidTreeNode.new(nil, doc_hash: child_hash) }
      end
    end
  end
end
