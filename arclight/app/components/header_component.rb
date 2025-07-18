
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
          placeholder_text: I18n.t("oac.search.placeholder_text"),
          url: helpers.search_action_path,
          params: params
          #   autocomplete_path: "/catalog/suggest"
        )
    end
end
