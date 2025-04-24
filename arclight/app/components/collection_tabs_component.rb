
class CollectionTabsComponent < ViewComponent::Base
  def initialize(document: nil, access: nil)
    @document = document
    @access = access
  end

  def has_companion_guides?
    # Evetually, add logic to determine if the document in question has companion guides. For now, just always true
    true
  end

  def access
    # passthrough of the Arclight Document Presenter access method
    @access
  end
end
