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

    if response.grouped? and response.grouped.first.group["groups"].present?
      collection_hash = response.grouped.first.group["groups"].first["doclist"]["docs"].first["collection"]["docs"].first
    elsif response.documents.present?
      collection_hash = response.documents.first["collection"]["docs"].first
    else
      # TODO: When there are no search results, but a Collection filter
      # has been selected, we should still be able to display the Collection.
      return nil
    end
    collection = ::SolrDocument.new(collection_hash)
  end

  def show_static_finding_aid_link?(document)
    _within_child_component_limit?(document) && _not_in_disallow_list(document)
  end

  def _within_child_component_limit?(document)
    document.total_component_count.to_i < Rails.application.config.child_component_limit
  end

  def _not_in_disallow_list(document)
    !Rails.application.config.disallowed_static_guides.include? document.id
  end

  def ark_rewrite_link_to(resource)
    if resource.href =~ /.*ark\.cdlib\.org.*/
      href = resource.href.gsub(/ark\.cdlib\.org/, "oac.cdlib.org")
      label = resource.label.gsub(/ark\.cdlib\.org/, "oac.cdlib.org")
      return link_to(label, href)
    end

    link_to(resource.label, resource.href)
  end

  # Overwrite the dynamically generated path helper methods provided by Rails
  # to avoid encoding slashes in ARK identifiers. These methods are generated
  # at runtime, and super, here, refers to the original method.
  #
  # This allows us to use the standard Rails path helpers in our code (and, more
  # importantly, in Blacklight and Arclight) without changing any of that code.
  #
  # Sometimes, Rails does get confused and doesn't find our overrides.
  # helpers.<method_name> most reliably finds the correct method.
  def hierarchy_solr_document_path(*args, **options)
    Rails.logger.debug("custom oac hierarchy_solr_document_path generated")
    rewrite_ark_path_if_needed(*args, **options) { super(*args, **options) }
  end

  def solr_document_path(*args, **options)
    Rails.logger.debug("custom oac solr_document_path generated")
    rewrite_ark_path_if_needed(*args, **options) { super(*args, **options) }
  end

  def static_finding_aid_path(*args, **options)
    Rails.logger.debug("custom oac static_finding_aid_path generated")
    rewrite_ark_path_if_needed(*args, **options) { super(*args, **options) }
  end

  private

  def rewrite_ark_path_if_needed(*args, **options)
    document_id = options[:id] || (args.first.respond_to?(:id) ? args.first.id : args.first)
    # yield refers to the block passed to this method, "super", above. In each case, super
    # refers to the Rails-generated path helper method - a dynamically generated method.
    encoded_path = yield

    Rails.logger.debug("Generated path from original: #{encoded_path}")

    if document_id.to_s.start_with?("ark:")
      Rails.logger.debug("ARK detected, generating custom path.")
      encoded_path.gsub!("%2F", "/")
      Rails.logger.debug("Rewritten path: #{encoded_path}")
    end
    encoded_path
  end

  def rewrite_any_ark_path(path)
    path.include?("ark:") ? path.gsub("%2F", "/") : path
  end

  def render_html_revision(args)
    values = Array(args[:value])
    simple_format(Array(args[:value]).flatten.join('<br/><br/>'))
  end
end
