# frozen_string_literal: true

# component for rendering a digital content facet
class OnlineContentFacetComponent < Blacklight::FacetFieldListComponent
    def facet_toggle_url
        facet_item_presenter(@facet_field.paginator.items[0]).href
    end
end
