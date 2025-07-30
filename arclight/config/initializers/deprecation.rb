require "deprecation"
Rails.application.config.after_initialize do
  Deprecation.default_deprecation_behavior = :silence
end
