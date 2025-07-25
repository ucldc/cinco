# Set the number of how many child components is
# too many to display a static finding aid.
#
#
Rails.application.config.child_component_limit = ENV["CHILD_COMPONENT_LIMIT"] || 1700

#
enable_static_guide_cache = ENV["ENABLE_STATIC_GUIDE_CACHE"] || true
if enable_static_guide_cache == "false"
  Rails.application.config.enable_static_guide_cache = false
else
  Rails.application.config.enable_static_guide_cache = true
end

Rails.application.config.disallowed_static_guides = [
  "ark:/13030/c8tt4pp0"
]
