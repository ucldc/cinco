require "oac/finding_aid_tree_node"

class StaticFindingAidController < CatalogController
  layout "static_catalog_result"

  configure_blacklight do |config|
    config.header_component = BlankComponent
    config.show.document_component = StaticFindingAid::DocumentComponent
    config.show.access_component = StaticFindingAid::AccessComponent
  end

  def show
    @doc_tree = Oac::FindingAidTreeNode.new(self, params[:id])
    @document = @doc_tree.document
  end
end
