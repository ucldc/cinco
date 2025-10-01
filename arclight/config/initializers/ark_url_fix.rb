Rails.application.config.to_prepare do
  Blacklight::UrlHelperBehavior.module_eval do
    def link_to_document(doc, field_or_opts = nil, opts = { counter: nil })
      if doc.id.to_s.start_with?("ark:")
        path = "/findaid/#{doc.id}"

        label = case field_or_opts
        when NilClass
          document_presenter(doc).heading
        when Hash
          opts = field_or_opts
          document_presenter(doc).heading
        else
          field_or_opts
        end

        original_url = search_state.url_for_document(doc)
        Rails.logger.info("Original URL: #{original_url}")
        Rails.logger.info("Rewritten URL: #{path}")

        link_to(label, path, document_link_params(doc, opts))
      else
        # Call the original method
        label = case field_or_opts
        when NilClass
          document_presenter(doc).heading
        when Hash
          opts = field_or_opts
          document_presenter(doc).heading
        else
          field_or_opts
        end

        link_to(label, search_state.url_for_document(doc), document_link_params(doc, opts))
      end
    end
  end
end
