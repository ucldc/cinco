# Added to get the latest version of this file, which includes
# an aria label for accessibility.
# OAC Edits:
#   - Removed tag.span class: d-md-inline
#   - Replace single quotes with double quotes, per rubocop

# frozen_string_literal: true

module Blacklight
  class SearchButtonComponent < Blacklight::Component
    def initialize(text:, id:)
      @text = text
      @id = id
    end

    def call
      tag.button(class: "btn btn-primary search-btn", type: "submit", id: @id, aria: { label: @text }) do
        tag.span(@text, class: "d-none me-sm-1 submit-search-text", aria: { hidden: true }) +
          render(Blacklight::Icons::SearchComponent.new)
      end
    end
  end
end
