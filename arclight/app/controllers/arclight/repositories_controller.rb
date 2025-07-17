# Blacklight::Solr::Repository

module Arclight
    class RepositoriesController < ApplicationController
        def index
            @repositories = Arclight::Repository.all
            @repository_list = @repositories.group_by { |r| r.name[0] }
            load_collection_counts
        end

        def home
            @repositories = Arclight::Repository.all
        end

        def show
            query = _id_or_name(params[:id])
            repository = Arclight::Repository.find_by!(**query)
            url = search_action_url(
                f: {
                  repository: [ repository.name ],
                  level: [ "Collection" ]
                },
                sort: "title_sort asc"
            )
            redirect_to url
        end

        private

        def _id_or_name(params_id)
          # if it has a '+' in the string, it's probably a name
          if params_id.include?("+")
            return { name: params_id.gsub("+", " ").gsub("::", ", ") }
          end
          { slug: params_id }
        end

        def load_collection_counts
            counts = fetch_collection_counts
            @repositories.each do |repository|
            repository.collection_count = counts[repository.name] || 0
            end
        end

        def fetch_collection_counts
            search_service = Blacklight.repository_class.new(blacklight_config)
            results = search_service.search(
            q: "level_ssim:Collection",
            'facet.field': "repository_ssim",
            fq: "preview_ssi:false", # exclude previewed finding aids from collections counts
            rows: 0
            )
            Hash[*results.facet_fields["repository_ssim"]]
        end
    end
end
