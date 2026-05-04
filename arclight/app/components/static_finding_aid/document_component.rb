module StaticFindingAid
  class DocumentComponent < Arclight::DocumentComponent
    def initialize(document: nil, presenter: nil, partials: nil,
      id: nil, classes: [], component: :article, title_component: nil,
      counter: nil, document_counter: nil, counter_offset: 0,
      show: false, doc_tree: nil, **args)
      super
      @document_tree = doc_tree
      @tree_level = args[:tree_level] || 0
    end

    def document_tree
      @document_tree
    end

    def tree_level
      @tree_level
    end

    def search_state
      Blacklight::SearchState.new({}, blacklight_config)
    end

    def should_render_field?(field_config, *args)
      true
    end
  end
end
