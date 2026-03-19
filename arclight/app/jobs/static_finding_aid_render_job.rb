class StaticFindingAidRenderJob < ApplicationJob
  include StaticFindingAid::S3Cache

  queue_as :default

  # Serialize all expensive Solr tree fetches so concurrent jobs don't pile up
  # on Solr. Jobs waiting on the lock will short-circuit via the S3 cache guard
  # once the first job completes.
  @@render_mutex = Mutex.new

  def perform(id)
    Rails.logger.info("StaticFindingAidRenderJob: starting #{id}")

    document = fetch_document_metadata(id)
    unless document
      Rails.logger.warn("StaticFindingAidRenderJob: no document found for #{id}, skipping")
      return
    end

    if s3_cache_current?(id, document)
      Rails.logger.info("StaticFindingAidRenderJob: S3 cache already current for #{id}, skipping")
      return
    end

    @@render_mutex.synchronize do
      # Re-check inside the lock — a preceding job may have just finished
      if s3_cache_current?(id, document)
        Rails.logger.info("StaticFindingAidRenderJob: S3 cache current after acquiring lock for #{id}, skipping")
        return
      end

      Rails.logger.info("StaticFindingAidRenderJob: rendering #{id}")

      doc_tree = Oac::FindingAidTreeNode.new(StaticFindingAidController, id)

      # ActionController::Renderer creates a bare controller instance without
      # calling `process`, so `action_name` is never set. Blacklight uses
      # `action_name` to choose ShowPresenter vs IndexPresenter; without "show"
      # it falls back to IndexPresenter which lacks `with_field_group`. Override
      # it via an anonymous subclass so the renderer context always returns "show".
      renderer_class = Class.new(StaticFindingAidController) do
        def action_name
          "show"
        end
      end
      renderer = renderer_class.renderer.new("rack.session" => {})
      main_content = renderer.render(
        partial: "static_finding_aid/show_main_content",
        assigns: {
          doc_tree: doc_tree,
          document: doc_tree.document,
          search_context: {},
          current_search_session: nil
        }
      )

      upload_to_s3(id, main_content, doc_tree.document)
      Rails.logger.info("StaticFindingAidRenderJob: finished #{id}")
    end
  end

  private

  # Cheap Solr query - only the fields needed for cache validation
  def fetch_document_metadata(id)
    repository = Blacklight.repository_class.new(StaticFindingAidController.blacklight_config)
    response = repository.search(
      q: "id:#{RSolr.solr_escape(id)}",
      fl: "_version_,timestamp,total_component_count_is",
      rows: 1,
    )
    doc = response["response"]["docs"].first
    SolrDocument.new(doc) if doc
  end
end
