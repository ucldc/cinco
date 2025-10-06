# frozen_string_literal: true

module Oac
  # Render the hierarchy for a document
  class SimpleBreadcrumbsHierarchyComponent < ViewComponent::Base
    delegate :document, to: :@presenter

    def initialize(presenter:)
      super

      @presenter = presenter
      collections, @parents_under_collection = document.parents.partition(&:collection?)
      @collection = collections.first
    end

    attr_reader :collection, :parents_under_collection
  end
end
