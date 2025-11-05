# frozen_string_literal: true

class OacIndexPresenter < Blacklight::IndexPresenter
  # Override blacklight configuration behavior to
  # allow us to use fallback field values
  def heading
    if @document.title_filing
      @document.title_filing
    elsif @document.unittitle
      @document.unittitle
    else
      @document.id
    end
  end
end
