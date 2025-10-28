# frozen_string_literal: true

class OacIndexPresenter < Blacklight::IndexPresenter
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
