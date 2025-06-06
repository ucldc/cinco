# frozen_string_literal: true

module Oac
  # Override Blacklight's SearchBarComponent to add a dropdown for choosing
  # the context of the search (within "this collection" or "all collections").
  # If a collection has not been chosen, it displays a dropdown with only "all collections"
  # as the only selectable option.
  class SearchBarComponent < Arclight::SearchBarComponent
    def initialize(**kwargs)
        @placeholder_text = kwargs[:placeholder_text]
        kwargs.delete(:placeholder_text)
        super
        @kwargs = kwargs
    end
  end
end
