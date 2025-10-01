# frozen_string_literal: true

module StaticFindingAidHelper
  def static_show_content_classes
    "col-12  show-document"
  end

  def link_back_to_catalog(opts = { label: nil })
    ""
  end

  def link_to_name_facet(args)
  end

  def oac_static_finding_aid_path(*args, **options)
    document_id = options[:id] || (args.first.respond_to?(:id) ? args.first.id : args.first)

    encoded_path = static_finding_aid_path(*args, **options)
    Rails.logger.info("Generated path from original: #{encoded_path}")

    if document_id.to_s.start_with?("ark:")
      Rails.logger.info("ARK detected, generating custom static finding aid path.")
      encoded_path.gsub!("%2F", "/")
      Rails.logger.info("Rewritten static finding aid path: #{encoded_path}")
    end
    encoded_path
  end
end
