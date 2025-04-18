# frozen_string_literal: true

require "arclight/exceptions"

module Oac
  ##
  # A utility class to normalize titles, typically by joining
  # the title and date, e.g., "My Title, 1990-2000"
  class NormalizedComponentTitle
    # @param [String] `title` from the `unittitle`
    # @param [String] `date` from the `unitdate`
    # @param [String] `container_label` from `container`
    # @param [String] `unitid` from the `unitid`
    def initialize(title, date = nil, container_label = nil, unitid = nil)
      @title = title.gsub(/\s*,\s*$/, "").strip if title.present?
      @date = date.strip if date.present?
      @container_label = container_label if container_label.present?
      @unitid = unitid if unitid.present?
    end

    # @return [String] the normalized title/date
    def to_s
      normalize
    end

    private

    attr_reader :title, :date, :container_label, :unitid, :default

    def normalize
      result = [ title, date ].compact.join(", ")
      result = container_label if result.blank?
      result = unitid if result.blank?

      raise Arclight::Exceptions::TitleNotFound if result.blank?

      result
    end
  end
end
