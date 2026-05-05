# frozen_string_literal: true

module Oac
  # Render digital object links for a document
  class EmbedComponent < Arclight::EmbedComponent
    def initialize(heading_level: :h2, **kwargs)
      super(**kwargs)
      @heading_level = heading_level
    end

    def heading_level
      @heading_level
    end
  end
end
