# Set the number of how many child components is
# too many to display a static finding aid.
#
#
Rails.application.config.child_component_limit = ENV["CHILD_COMPONENT_LIMIT"] || 1700

#
Rails.application.config.disallowed_static_guides = [
  "ark:/13030/c8tt4pp0"
]
