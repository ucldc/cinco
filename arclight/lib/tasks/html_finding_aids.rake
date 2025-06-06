require "erb"

namespace :oac do
  task :html_finding_aid, [ :id ] => [ :environment ] do |t, args|
    id = args[:id]
    tree = FindingAidTree.new(id)
    binding.pry
    puts tree.render
  end
end

class FindingAidTreeNode
  attr_reader :data


  def method_missing(m, *args, &block)
    @data.send(m, *args, &block)
  end

  def initialize(id, has_children: true)
    blacklight_config = CatalogController.new.blacklight_config
    @repository = Blacklight.repository_class.new(blacklight_config)
    @data = SolrDocument.new(@repository.find(id).response["docs"][0])

    @hierarchy_data = @repository.search(
      { fq: "_nest_parent_:#{id}", sort: "sort_isi asc", facet: false }
    ).response["docs"] if has_children || []
  end

  def children
    @children ||= @hierarchy_data.map do  |item|
      doc = SolrDocument.new(item)
      parent = parent
      FindingAidTreeNode.new(doc.id, has_children: doc.children?)
    end
  end

  def render
    path = Rails.root.join("app/views/oac/static_html/#{@data.level}.html.erb")
    template = ERB.new(file = File.open(path).read)
    template.result(binding)
    # render the contents of the object itself
    # render the child contents
  end
end

class FindingAidTree < FindingAidTreeNode
  def collection_data
    @data
  end

  def render_front_matter
    pass
  end
end


namespace :static do
  desc "Generate a static HTML rendering of a finding aid and its full hierarchy"
  task :generate, [ :id ] => :environment do |t, args|
    id = args[:id]
    unless id.present?
      puts "Usage: rake static:generate[oac:1234]"
      exit 1
    end

    # ── 2. Fetch the Solr document exactly as Arclight would
    #    We can lean on your existing CatalogController#fetch
    controller = CatalogController.new
    binding.pry
    document = controller.search_service.fetch(id)

    # ── 3. Wrap it in Arclight’s presenter
    presenter = Arclight::DocumentPresenter.new(document, controller.view_context)

    # ── 4. Use Rails’ renderer to render your `catalog/static` template
    #    (this template is the same one you’d have in app/views/catalog/static.html.erb)
    renderer = ApplicationController.renderer.new(http_host: ENV["HOST"] || "localhost")
    html     = renderer.render(
      template: "oac/static_html",
      assigns:  { presenter: presenter }
    )

    puts html
  end
end
