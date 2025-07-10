module StaticFindingAid
  class DocumentComponent < Arclight::DocumentComponent
    def initialize(document: nil, presenter: nil, partials: nil,
      id: nil, classes: [], component: :article, title_component: nil,
      counter: nil, document_counter: nil, counter_offset: 0,
      show: false, doc_tree: nil, **args)
      super
      @document_tree = doc_tree
    end

    def document_tree
      @document_tree
    end

    def search_state
      {}
    end

    def should_render_field?(field_config, *args)
      true
    end
  end
end
