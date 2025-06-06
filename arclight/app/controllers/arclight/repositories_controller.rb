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
            repository = Arclight::Repository.find_by!(slug: params[:id])
            url = search_action_url(
                f: {
                  repository: [ repository.name ],
                  level: [ "Collection" ]
                }
            )
            redirect_to url
        end

        private

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
