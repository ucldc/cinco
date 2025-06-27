module ApplicationHelper
  include Blacklight::LocalePicker::LocaleHelper

  def additional_locale_routing_scopes
    [ blacklight, arclight_engine ]
  end

  def repository_location_to_city(location_str)
    location_html = Nokogiri::HTML.fragment(location_str)
    city_content = location_html.at('div[class="al-repository-street-address-city_state_zip_country"]').text
    re = /(([A-Z][a-z]+\s?)+),\s([A-Z]{2})/
    m = re.match(city_content)
    if m
      m[0]
    else
      location_html
    end
  end

  def collection_faceted_on(search_service)
    collections = search_state.filter("collection").values
    return nil if collections.empty? or not collections.one?

    response, documents = search_service.search_results

    if response.grouped?
      collection_hash = response.grouped.first.group["groups"].first["doclist"]["docs"].first["collection"]["docs"].first
    else
      collection_hash = response.documents.first["collection"]["docs"].first
    end
    collection = ::SolrDocument.new(collection_hash)
  end
end
