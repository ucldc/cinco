# Set the number of how many child components is
# too many to display a static finding aid.
#
#
Rails.application.config.child_component_limit = ENV["CHILD_COMPONENT_LIMIT"] || 4500
