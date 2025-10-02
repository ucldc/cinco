# frozen_string_literal: true

module Arclight
  # Draw the links to the collection info in the sidebar
  class CollectionSidebarComponent < ViewComponent::Base
    def initialize(document:, partials:, collection_presenter:)
      super

      @document = document
      @partials = Array(partials)
      @collection_presenter = collection_presenter
    end

    attr_reader :document, :partials, :collection_presenter

    def has_section?(section)
      # Access field data comes from repositories.yml not from solr, so handle it in a different way.
      return true if section == :access_field

      collection_presenter.with_field_group(section).fields_to_render.any?
    end

    def document_section_path(section)
      [ document_path, section_anchor(section) ].join
    end

    def section_label(section)
      t("arclight.views.show.sections.#{section}")
    end

    def document_path
      @document_path ||= helpers.solr_document_path(document.root)
    end

    def section_anchor(section)
      "##{t("arclight.views.show.sections.#{section}").parameterize}"
    end

    def collection_number
      if @document.collection["unitid_tesim"].blank?
        @document.collection["ead_ssi"]
      else
        Array(@document.collection["unitid_tesim"]).join(", ")
      end
    end
  end
end
