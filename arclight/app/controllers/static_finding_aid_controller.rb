require "net/http"
require "oac/finding_aid_tree_node"
require "uri"

class StaticFindingAidController < ApplicationController
  layout "static_catalog_result"
  include Blacklight::Catalog
  include Arclight::Catalog
  include CacheControl

  configure_blacklight do |config|
    config.search_builder_class = StaticFindingAidSearchBuilder
    config.header_component = BlankComponent

    config.show.document_component = StaticFindingAid::DocumentComponent
    config.show.access_component = StaticFindingAid::AccessComponent
    config.track_search_session.storage = false

    config.default_solr_params = {
      rows: 10,
      fl: "*,collection:[subquery]",
      'collection.q': "{!terms f=id v=$row._root_}",
      'collection.defType': "lucene",
      'collection.fl': "*",
      'collection.rows': 1,
      fq: "preview_ssi:false"
    }


    config.default_document_solr_params = {
     qt: "document",
     fl: "*,collection:[subquery]",
     'collection.q': "{!terms f=id v=$row._root_}",
     'collection.defType': "lucene",
     'collection.fl': "*",
     'collection.rows': 1
    }

    config.add_results_document_tool(:online, component: Arclight::OnlineStatusIndicatorComponent)
    # config.add_results_document_tool(:arclight_bookmark_control, component: Arclight::BookmarkComponent)


    config.show.sidebar_component = Arclight::SidebarComponent
    config.show.breadcrumb_component = Arclight::SimpleBreadcrumbsHierarchyComponent
    config.show.embed_component = Arclight::EmbedComponent
    config.show.online_status_component = Arclight::OnlineStatusIndicatorComponent
    config.show.document_header_component = Arclight::BlankComponent
    config.show.display_type_field = "level_ssm"
    # config.show.thumbnail_field = 'thumbnail_path_ss'
    config.show.document_presenter_class = Arclight::ShowPresenter
    config.show.metadata_partials = %i[
      summary_field
      background_field
      related_field
      indexed_terms_field
      access_field
    ]

    config.show.collection_access_items = %i[
      terms_field
      cite_field
      in_person_field
      contact_field
    ]

    config.show.component_metadata_partials = %i[
      component_field
      component_indexed_terms_field
    ]

    config.show.component_access_items = %i[
      component_terms_field
      cite_field
      in_person_field
      contact_field
    ]

    # These are the parameters passed through in search_state.params_for_search
    config.search_state_fields += %i[id group hierarchy_context original_document]
    config.search_state_fields << { original_parents: [] }

    # ===========================
    # COLLECTION SHOW PAGE FIELDS
    # ===========================

    # Collection Show Page - Summary Section
    config.add_summary_field "creators", field: "creator_ssim", link_to_facet: false
    config.add_summary_field "abstract", field: "abstract_html_tesm", helper_method: :render_html_tags
    config.add_summary_field "extent", field: "extent_ssm"
    config.add_summary_field "language", field: "language_ssim"
    config.add_summary_field "prefercite", field: "prefercite_html_tesm", helper_method: :render_html_tags

    # Collection Show Page - Background Section
    config.add_background_field "scopecontent", field: "scopecontent_html_tesm", helper_method: :render_html_tags
    config.add_background_field "bioghist", field: "bioghist_html_tesm", helper_method: :render_html_tags
    config.add_background_field "acqinfo", field: "acqinfo_ssim", helper_method: :render_html_tags
    config.add_background_field "appraisal", field: "appraisal_html_tesm", helper_method: :render_html_tags
    config.add_background_field "custodhist", field: "custodhist_html_tesm", helper_method: :render_html_tags
    config.add_background_field "processinfo", field: "processinfo_html_tesm", helper_method: :render_html_tags
    config.add_background_field "arrangement", field: "arrangement_html_tesm", helper_method: :render_html_tags
    config.add_background_field "accruals", field: "accruals_html_tesm", helper_method: :render_html_tags
    config.add_background_field "phystech", field: "phystech_html_tesm", helper_method: :render_html_tags
    config.add_background_field "physloc", field: "physloc_html_tesm", helper_method: :render_html_tags
    config.add_background_field "physdesc", field: "physdesc_tesim", helper_method: :render_html_tags
    config.add_background_field "physfacet", field: "physfacet_tesim", helper_method: :render_html_tags
    config.add_background_field "dimensions", field: "dimensions_tesim", helper_method: :render_html_tags
    config.add_background_field "materialspec", field: "materialspec_html_tesm", helper_method: :render_html_tags
    config.add_background_field "fileplan", field: "fileplan_html_tesm", helper_method: :render_html_tags
    config.add_background_field "descrules", field: "descrules_ssm", helper_method: :render_html_tags
    config.add_background_field "note", field: "note_html_tesm", helper_method: :render_html_tags

    # Collection Show Page - Related Section
    config.add_related_field "relatedmaterial", field: "relatedmaterial_html_tesm", helper_method: :render_html_tags
    config.add_related_field "separatedmaterial", field: "separatedmaterial_html_tesm", helper_method: :render_html_tags
    config.add_related_field "otherfindaid", field: "otherfindaid_html_tesm", helper_method: :render_html_tags
    config.add_related_field "altformavail", field: "altformavail_html_tesm", helper_method: :render_html_tags
    config.add_related_field "originalsloc", field: "originalsloc_html_tesm", helper_method: :render_html_tags
    config.add_related_field "odd", field: "odd_html_tesm", helper_method: :render_html_tags

    # Collection Show Page - Indexed Terms Section
    config.add_indexed_terms_field "access_subjects", field: "access_subjects_ssim", link_to_facet: false, separator_options: {
      words_connector: "<br/>",
      two_words_connector: "<br/>",
      last_word_connector: "<br/>"
    }

    config.add_indexed_terms_field "names_coll", field: "names_coll_ssim", separator_options: {
      words_connector: "<br/>",
      two_words_connector: "<br/>",
      last_word_connector: "<br/>"
    }, link_to_facet: false

    config.add_indexed_terms_field "places", field: "places_ssim", link_to_facet: false, separator_options: {
      words_connector: "<br/>",
      two_words_connector: "<br/>",
      last_word_connector: "<br/>"
    }

    config.add_indexed_terms_field "indexes", field: "indexes_html_tesm",
                                              helper_method: :render_html_tags

    # ==========================
    # COMPONENT SHOW PAGE FIELDS
    # ==========================

    # Component Show Page - Metadata Section
    config.add_component_field "containers", accessor: "containers", separator_options: {
      words_connector: ", ",
      two_words_connector: ", ",
      last_word_connector: ", "
    }, if: lambda { |_context, _field_config, document|
      document.containers.present?
    }
    config.add_component_field "creators", field: "creator_ssim", link_to_facet: false
    config.add_component_field "abstract", field: "abstract_html_tesm", helper_method: :render_html_tags
    config.add_component_field "extent", field: "extent_ssm"
    config.add_component_field "scopecontent", field: "scopecontent_html_tesm", helper_method: :render_html_tags
    config.add_component_field "language", field: "language_ssim"
    config.add_component_field "acqinfo", field: "acqinfo_ssim", helper_method: :render_html_tags
    config.add_component_field "bioghist", field: "bioghist_html_tesm", helper_method: :render_html_tags
    config.add_component_field "appraisal", field: "appraisal_html_tesm", helper_method: :render_html_tags
    config.add_component_field "custodhist", field: "custodhist_html_tesm", helper_method: :render_html_tags
    config.add_component_field "processinfo", field: "processinfo_html_tesm", helper_method: :render_html_tags
    config.add_component_field "arrangement", field: "arrangement_html_tesm", helper_method: :render_html_tags
    config.add_component_field "accruals", field: "accruals_html_tesm", helper_method: :render_html_tags
    config.add_component_field "phystech", field: "phystech_html_tesm", helper_method: :render_html_tags
    config.add_component_field "materialspec", field: "materialspec_html_tesm", helper_method: :render_html_tags
    config.add_component_field "physloc", field: "physloc_html_tesm", helper_method: :render_html_tags
    config.add_component_field "physdesc", field: "physdesc_tesim", helper_method: :render_html_tags
    config.add_component_field "physfacet", field: "physfacet_tesim", helper_method: :render_html_tags
    config.add_component_field "dimensions", field: "dimensions_tesim", helper_method: :render_html_tags
    config.add_component_field "fileplan", field: "fileplan_html_tesm", helper_method: :render_html_tags
    config.add_component_field "altformavail", field: "altformavail_html_tesm", helper_method: :render_html_tags
    config.add_component_field "otherfindaid", field: "otherfindaid_html_tesm", helper_method: :render_html_tags
    config.add_component_field "odd", field: "odd_html_tesm", helper_method: :render_html_tags
    config.add_component_field "relatedmaterial", field: "relatedmaterial_html_tesm", helper_method: :render_html_tags
    config.add_component_field "separatedmaterial", field: "separatedmaterial_html_tesm", helper_method: :render_html_tags
    config.add_component_field "originalsloc", field: "originalsloc_html_tesm", helper_method: :render_html_tags
    config.add_component_field "note", field: "note_html_tesm", helper_method: :render_html_tags

    # Component Show Page - Indexed Terms Section
    config.add_component_indexed_terms_field "access_subjects", field: "access_subjects_ssim", link_to_facet: false, separator_options: {
      words_connector: "<br/>",
      two_words_connector: "<br/>",
      last_word_connector: "<br/>"
    }

    config.add_component_indexed_terms_field "names", field: "names_ssim", separator_options: {
      words_connector: "<br/>",
      two_words_connector: "<br/>",
      last_word_connector: "<br/>"
    }, link_to_facet: false

    config.add_component_indexed_terms_field "places", field: "places_ssim", link_to_facet: false, separator_options: {
      words_connector: "<br/>",
      two_words_connector: "<br/>",
      last_word_connector: "<br/>"
    }

    config.add_component_indexed_terms_field "indexes", field: "indexes_html_tesm",
                                              helper_method: :render_html_tags

    # =================
    # ACCESS TAB FIELDS
    # =================

    # Collection Show Page Access Tab - Terms and Conditions Section
    config.add_terms_field "restrictions", field: "accessrestrict_html_tesm", helper_method: :render_html_tags
    config.add_terms_field "terms", field: "userestrict_html_tesm", helper_method: :render_html_tags

    # Component Show Page Access Tab - Terms and Condition Section
    config.add_component_terms_field "restrictions", field: "accessrestrict_html_tesm", helper_method: :render_html_tags
    config.add_component_terms_field "terms", field: "userestrict_html_tesm", helper_method: :render_html_tags
    config.add_component_terms_field "parent_restrictions", field: "parent_access_restrict_tesm", helper_method: :render_html_tags
    config.add_component_terms_field "parent_terms", field: "parent_access_terms_tesm", helper_method: :render_html_tags

    # Collection and Component Show Page Access Tab - In Person Section
    config.add_in_person_field "repository_location", values: ->(_, document, _) { document.repository_config }, component: Arclight::RepositoryLocationComponent
    config.add_in_person_field "before_you_visit", values: ->(_, document, _) { document.repository_config&.visit_note }

    # Collection and Component Show Page Access Tab - How to Cite Section
    config.add_cite_field "prefercite", field: "prefercite_html_tesm", helper_method: :render_html_tags

    # Collection and Component Show Page Access Tab - Contact Section
    config.add_contact_field "repository_contact", values: ->(_, document, _) { document.repository_config&.contact }

    # Group header values
    config.add_group_header_field "abstract_or_scope", accessor: true, truncate: true, helper_method: :render_html_tags
  end

  def show
    @document = search_service.fetch(::RSolr.solr_escape(params[:id]))

      # make a head request to S3
      s3_bucket = ENV["S3_BUCKET"]
      uri_string = "https://#{s3_bucket}.s3.us-west-2.amazonaws.com/static_findaids/static_findaids/#{@document.id}.html"
      uri = URI(uri_string)
      response = nil
      Net::HTTP.start(uri.hostname, 80) { |http|
        response = http.head(uri.path)
      }

      case response
      when Net::HTTPOK
        redirect_to "/static_findaids/#{@document.id}.html"
      end

      if !helpers.show_static_finding_aid_link?(@document)
        redirect_to "/findaid/#{@document.id}"
      end

    @doc_tree = Oac::FindingAidTreeNode.new(self, params[:id])
  end
end
