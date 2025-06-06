class StaticFindingAidsController < CatalogController
  configure_blacklight do |config|
    config.header_component = BlankComponent
  end

  def show
    @doc_tree = FindingAidTreeNode.new(self, params[:id])
    @document = @doc_tree.data
  end
end


class FindingAidTreeNode
  attr_reader :data


  def method_missing(m, *args, &block)
    @data.send(m, *args, &block)
  end

  def initialize(controller, id, has_children: true)
    @data = controller.search_service.fetch(id)
    @hierarchy_data = controller.search_service()
  end

  def children
    @children ||= @hierarchy_data.map do  |item|
      FindingAidTreeNode.new(doc.id, has_children: doc.children?)
    end
  end
end
