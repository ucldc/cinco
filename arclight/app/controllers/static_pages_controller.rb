class StaticPagesController < ApplicationController
  def about
  end

  def faqs
  end

  def help
  end

  def termsofuse
  end

  def privacy
  end

  def accessibility
  end

  def home
    @repositories = Arclight::Repository.all
  end
end
