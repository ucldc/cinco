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
      params = params.dup

      # Remove Level: Collection filter if it exists
      if params[:f] && params[:f][:level] == [ "Collection" ]
          params[:f].delete(:level)
          params.delete(:f) if params[:f].empty?
          # If we're removing the level filter, we can assume we're
          # searching from a canned repository search results set,
          # and we want to "reset" canned parameters to the search
          # bar defaults - Group by Collection & Sort by Relevance
          params[:group] = true
          params.delete(:sort)
        # params[:sort] = "score desc, title_sort asc"
      end

      if params[:f] && params[:f][:repository]
        placeholder_text = "Search this institution"
      elsif params[:f] && params[:f][:collection]
        placeholder_text = "Search this collection"
      else
        placeholder_text = I18n.t("oac.search.placeholder_text")
      end

      Oac::SearchBarComponent.new(
        placeholder_text: placeholder_text,
        url: helpers.search_action_url,
        params: params
      )
    end
  end
end
