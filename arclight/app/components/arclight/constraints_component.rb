# frozen_string_literal: true

module Arclight
  # Extend the upstream constraints with breadcrumbs and
  # repository context information
  class ConstraintsComponent < Blacklight::ConstraintsComponent
    def initialize(**kwargs)
      super

      @kwargs = kwargs
    end

    def repository
      @repository ||= helpers.repository_faceted_on
    end

    def search_bar
      render search_bar_component
    end

    def search_bar_component
      params = helpers.search_state.params_for_search.except(:qt)
      params[:group] = true
      params["f[repository][]"] = repository.name
      params.delete("f[level][]")
      Oac::SearchBarComponent.new(
        placeholder_text: "Search this repository",
        url: helpers.search_action_url,
        params: params
      )
    end
  end
end
