# Set the number of how many child components is
# too many to display a static finding aid.
#
#
# Rails.application.config.child_component_limit = ENV["CHILD_COMPONENT_LIMIT"] || 10000
Rails.application.config.static_findaid_cache_transition = ENV["STATIC_FINDAID_CACHE_TRANSITION"] || false
#
Rails.application.config.disallowed_static_guides = [
  "ark:/13030/c8tt4pp0"
]

# Configure AWS/MinIO for local development
if ENV["CINCO_MINIO_ENDPOINT"].present?
  Aws.config.update(
    endpoint: ENV["CINCO_MINIO_ENDPOINT"],
    access_key_id: "minioadmin",
    secret_access_key: "minioadmin",
    force_path_style: true,
    region: "us-east-1"
  )

  ENV["S3_BUCKET"] ||= "cinco-dev"
end
