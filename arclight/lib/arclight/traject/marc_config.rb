# A sample traject configuration, save as say `traject_config.rb`, then
# run `traject -c traject_config.rb marc_file.marc` to index to
# solr specified in config file, according to rules specified in
# config file

require "securerandom"

require "traject"
require "traject_plus"
require "traject_plus/macros"
require "traject/nokogiri_reader"
require "arclight/repository"
require "arclight/normalized_date"
require "arclight/normalized_title"

require "traject/indexer"
require "traject/macros/marc21"

require "json"
require "marc"

# To have access to various built-in logic
# for pulling things out of MARC21, like `marc_languages`
require "traject/macros/marc21_semantics"
extend  Traject::Macros::Marc21Semantics

# To have access to the traject marc format/carrier classifier
require "traject/macros/marc_format_classifier"
extend Traject::Macros::MarcFormats


settings do
  provide "id_normalizer", "Arclight::NormalizedId"
  provide "date_normalizer", "Arclight::NormalizedDate"
  provide "title_normalizer", "Arclight::NormalizedTitle"
  provide "solr_writer.commit_on_close", "false"
  provide "repository", ENV.fetch("REPOSITORY_ID", nil)
  provide "logger", Logger.new($stderr)
end

each_record do |_record, context|
  next unless settings["repository"]

  context.clipboard[:repository] = Arclight::Repository.find_by(
    slug: settings["repository"]
  ).name
end

to_field "id_ssm", extract_marc("099a", trim_punctuation: true)
to_field "ctrl_num_ssm", extract_marc("001", trim_punctuation: true)

to_field "id"  do |_record, accumulator, context|
  id = context.output_hash["id_ssm"]&.first
  id = context.output_hash["ctrl_num_ssm"]&.first if id.blank?
  id = "#{settings["repository"]}_" + SecureRandom.uuid if id.blank?
  id = id.sub(" ", "_")
  accumulator << id
end

to_field "unitid_ssm", extract_marc("099a")
to_field "unitid_tesim", extract_marc("099a")

to_field "eadid_ssm", extract_marc("099a")

to_field "ead_ssi" do |_record, accumulator, context|
  accumulator << context.output_hash["eadid_ssm"]&.first&.strip
end

to_field "title_ssm", extract_marc("245a")
to_field "title_tesim", extract_marc("245a")
to_field "unittitle_ssm", extract_marc("245a")
to_field "unitdate_ssm", extract_marc("245f")

to_field "main_persname_ssm", extract_marc("100a")
to_field "main_corpname_ssm", extract_marc("110a")

to_field "preview_ssi" do |_record, accumulator|
  accumulator << settings.fetch(:preview, "false")
end

# All top-level docs treated as 'collection' for routing / display purposes
to_field "level_ssm" do |_record, accumulator|
  accumulator << "collection"
end

to_field "level_ssim" do |record, accumulator|
  accumulator << "Collection"
end

to_field "normalized_date_ssm" do |_record, accumulator, context|
  accumulator << context.output_hash["unitdate_ssm"]&.first
end

to_field "normalized_title_ssm" do |_record, accumulator, context|
  title = context.output_hash["title_ssm"]&.first
  date = context.output_hash["normalized_date_ssm"]&.first
  accumulator << [ title, date ].compact.join(" ").to_s
end

to_field "oac_normalized_title_ssm" do |_record, accumulator, context|
  title = context.output_hash["unittitle_ssm"]&.first
  date = context.output_hash["normalized_date_ssm"]&.first
  accumulator << [ title, date ].compact.join(" ").to_s
end

to_field "collection_title_tesim" do |_record, accumulator, context|
  accumulator.concat context.output_hash.fetch("normalized_title_ssm", [])
end

to_field "collection_ssim" do |_record, accumulator, context|
  accumulator.concat context.output_hash.fetch("normalized_title_ssm", [])
end

to_field "oac_collection_ssim" do |_record, accumulator, context|
  accumulator.concat context.output_hash.fetch("oac_normalized_title_ssm", [])
end

to_field "repository_ssm" do |_record, accumulator, context|
  accumulator << context.clipboard[:repository]
end

to_field "repository_ssim" do |_record, accumulator, context|
  accumulator << context.clipboard[:repository]
end

to_field "geogname_ssm", extract_marc("651")
to_field "geogname_ssim", extract_marc("651")

to_field "creator_ssm", extract_marc("100:110:700:710")
to_field "creator_ssim", extract_marc("100:110:700:710")
# to_field "creator_sort", extract_marc("710")

to_field "creator_persname_ssim", extract_marc("100:700")
to_field "creator_corpname_ssim", extract_marc("110:710")

to_field "creators_ssim" do |_record, accumulator, context|
  accumulator.concat context.output_hash["creator_persname_ssim"] if context.output_hash["creator_persname_ssim"]
  accumulator.concat context.output_hash["creator_corpname_ssim"] if context.output_hash["creator_corpname_ssim"]
  accumulator.concat context.output_hash["creator_famname_ssim"] if context.output_hash["creator_famname_ssim"]
end

to_field "places_ssim", extract_marc("651")

to_field "access_terms_ssm", extract_marc("540a15")

to_field "acqinfo_ssim", extract_marc("541a19")
to_field "acqinfo_ssim", extract_marc("541a19")


to_field "access_subjects_ssim", extract_marc("600abcdtq:610abt:610x:611abt:611x:630aa:630x:648a:648x:650aa:650x:651a:651x:691a:691x:653aa:654ab:656aa:690a:690x",
          trim_punctuation: true,) do |record, accumulator|
  # upcase first letter if needed, in MeSH sometimes inconsistently downcased
  accumulator.collect! do |value|
    value.gsub(/\A[a-z]/) do |m|
      m.upcase
    end
  end
end

# to_field "access_subjects_ssm" do |_record, accumulator, context|
#   accumulator.concat context.output_hash["access_subjects_ssim"]
# end

to_field "has_online_content_ssim" do |_record, accumulator, context|
  accumulator << false
end

to_field "physdesc_tesim", extract_marc("300")

to_field "extent_ssm", extract_marc("300a")
to_field "extent_tesim" do |_record, accumulator, context|
  accumulator.concat context.output_hash["extent_ssm"] || []
end

to_field "physfacet_tesim", extract_marc("300b")
to_field "dimensions_tesim", extract_marc("300c")
to_field "genreform_ssim", extract_marc("655")

to_field "materialspec_tesim", extract_marc("254")
to_field "materialspec_html_tesm", extract_marc("254")

to_field "abstract_tesim", extract_marc("520a")
to_field "abstract_html_tesm", extract_marc("520a")

to_field "physloc_tesim", extract_marc("852z")
to_field "physloc_html_tesm", extract_marc("852z")

to_field "accessrestrict_tesim", extract_marc("506a")
to_field "accessrestrict_html_tesm", extract_marc("506a")

to_field "accruals_tesim", extract_marc("584a")
to_field "accruals_html_tesm", extract_marc("584a")

to_field "altformavail_tesim", extract_marc("530a")
to_field "altformavail_html_tesm", extract_marc("530a")

to_field "arrangement_tesim", extract_marc("351a")
to_field "arrangement_html_tesm", extract_marc("351a")

to_field "bibliography_tesim", extract_marc("581a")
to_field "bibliography_html_tesm", extract_marc("581a")

to_field "bioghist_tesim", extract_marc("545a")
to_field "bioghist_html_tesm", extract_marc("545a")

to_field "custodhist_tesim", extract_marc("561a")
to_field "custodhist_html_tesm", extract_marc("561a")

to_field "odd_tesim", extract_marc("500a")
to_field "odd_html_tesm", extract_marc("500a")

to_field "originalsloc_tesim", extract_marc("535")
to_field "originalsloc_html_tesm", extract_marc("535")

to_field "otherfindaid_tesim", extract_marc("555a")
to_field "otherfindaid_html_tesm", extract_marc("555a")

to_field "phystech_tesim", extract_marc("538")
to_field "phystech_html_tesm", extract_marc("538")

to_field "prefercite_tesim", extract_marc("524a")
to_field "prefercite_html_tesm", extract_marc("524a")

to_field "processinfo_tesim", extract_marc("583a")
to_field "processinfo_html_tesm", extract_marc("583a")

to_field "userestrict_tesim", extract_marc("540a")
to_field "userestrict_html_tesm", extract_marc("540a")

to_field "corpname_tesim", extract_marc("610")
to_field "corpname_html_tesm", extract_marc("610")

to_field "famname_tesim", extract_marc("600")
to_field "famname_html_tesm", extract_marc("600")

to_field "note_tesim", extract_marc("555a:506a")
to_field "note_html_tesm", extract_marc("555a:506a")

to_field "language_ssim", marc_languages

# count all descendant components from the top-level
to_field "total_component_count_is", first_only do |record, accumulator|
  accumulator << 0
end

# count all digital objects from the top-level
to_field "online_item_count_is", first_only do |record, accumulator|
  accumulator << 0
end

to_field "component_level_isim" do |_record, accumulator, _context|
  accumulator << 0
end

to_field "sort_isi" do |_record, accumulator, _context|
  accumulator << 0
end
