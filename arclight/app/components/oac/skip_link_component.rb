# frozen_string_literal: true

module Oac
  class SkipLinkComponent < Blacklight::SkipLinkComponent
    def search_id
      "#q"
    end
  end
end
