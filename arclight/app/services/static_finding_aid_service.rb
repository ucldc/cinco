class StaticFindingAidService
  include StaticFindingAid::S3Cache

  attr_reader :document, :doc_tree, :html_content

  def initialize(controller, id)
    @controller = controller
    @id = id
  end

  # Returns one of: :not_found, :cached, :rendered
  def call
    @document = @controller.search_service.fetch(::RSolr.solr_escape(@id))
    return :not_found unless @document

    if (cached_content = try_s3_cache)
      @html_content = cached_content
      return :cached
    end

    render_dynamic
    :rendered
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

    @doc_tree = Oac::FindingAidTreeNode.new(@controller, @id)
    @document = @doc_tree.document

    # Render and cache just the main content partial
    if ENV["S3_BUCKET"].present?
        # Render to string instead of responding
        @html_content = @controller.render_to_string(
            layout: "static_catalog_result",
            formats: [ :html ],
            assigns: { doc_tree: @doc_tree, document: @document }
        )
        upload_to_s3(@id, @html_content, @document)
    end
  end
end
