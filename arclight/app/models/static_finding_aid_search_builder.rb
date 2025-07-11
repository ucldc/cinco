# frozen_string_literal: true

class StaticFindingAidSearchBuilder < Blacklight::SearchBuilder
  include Blacklight::Solr::SearchBuilderBehavior
  include StaticFindingAid::SearchBehavior
end
