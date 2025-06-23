
# Extend ArcLight's HeaderComponent
# https://github.com/projectblacklight/arclight/blob/main/app/components/arclight/header_component.rb
class HeaderComponent < Arclight::HeaderComponent
    def search_bar
        render search_bar_component
    end

    def search_bar_component
        params = helpers.search_state.params_for_search.except(:qt, :q, :f)
        params[:group] = true
        Oac::SearchBarComponent.new(
          placeholder_text: "Search over 60,000 collection guides",
          url: helpers.search_action_url,
          params: params,
          autocomplete_path: "/catalog/suggest"
        )
    end
end
