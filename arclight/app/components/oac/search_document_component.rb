# frozen_string_literal: true

module Oac
  class SearchDocumentComponent < Blacklight::Component
      def initialize(document:, **kwargs)
        @document = document
      end

      def search_bar
        render search_bar_component
      end

      def search_bar_component
        params = helpers.search_state.params_for_search.except(:qt)
        params["f[collection][]"] = @document.collection.normalized_title

        Oac::SearchBarComponent.new(
          placeholder_text: "Search this collection",
          url: helpers.search_action_path(only_path: true),
          params: params
        )
      end
  end
end
