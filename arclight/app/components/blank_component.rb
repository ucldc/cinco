class BlankComponent < ViewComponent::Base
  # Renders nothing.
  # Use to remove what a component via Blacklight Config
  # instead of overriding a template
  erb_template <<~ERB
  ERB
end
