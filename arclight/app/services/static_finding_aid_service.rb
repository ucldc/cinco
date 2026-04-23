class StaticFindingAidService
  include StaticFindingAid::S3Cache

  SOLR_TREE_TIMEOUT_SECONDS = ENV.fetch("SOLR_TREE_TIMEOUT_SECONDS", 1).to_f

  attr_reader :document, :doc_tree, :html_content

  def initialize(controller, id)
    @controller = controller
    @id = id
  end

  # Returns one of: :not_found, :cached, :rendered, :timeout
  def call
    @document = @controller.search_service.fetch(::RSolr.solr_escape(@id))
    return :not_found unless @document

    if (cached_partial = try_s3_cache)
      @html_content = render_with_cached_partial(cached_partial)
      return :cached
    end

    start = Process.clock_gettime(Process::CLOCK_MONOTONIC)
    begin
      Timeout.timeout(SOLR_TREE_TIMEOUT_SECONDS) { render_dynamic }
      elapsed = Process.clock_gettime(Process::CLOCK_MONOTONIC) - start
      Rails.logger.info("Rendered static finding aid for #{@id} in #{elapsed.round(2)}s")
      :rendered
    rescue Timeout::Error
      elapsed = Process.clock_gettime(Process::CLOCK_MONOTONIC) - start
      Rails.logger.warn("Solr tree fetch timed out for #{@id} after #{elapsed.round(2)}s (limit: #{SOLR_TREE_TIMEOUT_SECONDS}s), queuing background render")
      StaticFindingAidRenderJob.perform_later(@id)
      :timeout
    end
  end

  private

  def try_s3_cache
    return nil unless ENV["S3_BUCKET"].present? && !Rails.application.config.disable_static_findaid_cache

    s3_content = fetch_from_s3("oac5/#{@id}.html", method(:cache_is_valid?), document: @document)
    s3_content ||= fetch_from_s3("static_findaids/#{@id}.html")
    s3_content
  end

  def render_dynamic
    Rails.logger.info("Rendering static finding aid for #{@id} dynamically")

    @doc_tree = Oac::FindingAidTreeNode.new(@id)
    @document = @doc_tree.document

    main_content = @controller.render_to_string(
      partial: "static_finding_aid/show_main_content",
      formats: [ :html ],
      assigns: { doc_tree: @doc_tree, document: @document }
    )

    # Render and cache just the main content partial
    if ENV["S3_BUCKET"].present?
      upload_to_s3(@id, main_content, @document)
    end

    # Render the full page for the immediate response using already-rendered partial
    @html_content = render_with_cached_partial(main_content)
  end

  def render_with_cached_partial(main_content)
    @controller.render_to_string(
      template: "static_finding_aid/show",
      layout: "static_catalog_result",
      formats: [ :html ],
      assigns: { document: @document, cached_main_content: main_content }
    )
  end
end
