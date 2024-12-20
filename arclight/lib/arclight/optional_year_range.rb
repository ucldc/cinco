# frozen_string_literal: true

require 'arclight/year_range'

module Arclight
  # A range of years that handles gaps, such as [1999, 2000, 2002].
  # Primary usage is:
  # ```
  # range = YearRange.new('1999/2004')
  # range.years => [1999, 2000, 2001, 2002, 2003, 2004]
  # range.to_s => '1999-2004'
  # range << range.parse_ranges(['2010/2010'])
  # range.years => [1999, 2000, 2001, 2002, 2003, 2004, 2010]
  # range.to_s => '1999-2004, 2010'
  # ```
  class OptionalYearRange < YearRange

    # @param [String] `dates` in the form YYYY/YYYY
    # @return [Array<Integer>] the set of years in the given range
    def parse_range(dates)
      return if dates.blank?

      start_year, end_year = dates.split('/').map { |date| to_year_from_iso8601(date) }
      return [start_year] if end_year.blank?

      return [] if (end_year - start_year) > 1000
      return [] unless start_year <= end_year

      (start_year..end_year).to_a
    end
  end
end
