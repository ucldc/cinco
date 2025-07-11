require "oac/finding_aid_tree_node"

class StaticFindingAidController < CatalogController
  layout "static_catalog_result"

  configure_blacklight do |config|
    config.header_component = BlankComponent
    config.show.document_component = StaticFindingAid::DocumentComponent
    config.show.access_component = StaticFindingAid::AccessComponent
    config.track_search_session.storage = false
    config[:summary_fields][:creators][:link_to_facet] = false
    config[:component_fields][:creators][:link_to_facet] = false
    config[:indexed_terms_fields][:access_subjects][:link_to_facet] = false
    config[:component_indexed_terms_fields][:access_subjects][:link_to_facet] = false
    config[:indexed_terms_fields][:places][:link_to_facet] = false
    config[:component_indexed_terms_fields][:places][:link_to_facet] = false
  end

  def show
    @doc_tree = Oac::FindingAidTreeNode.new(self, params[:id])
    @document = @doc_tree.document
  end
end
