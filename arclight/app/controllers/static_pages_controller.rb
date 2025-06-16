class StaticPagesController < ApplicationController
  def about
  end

  def help
  end

  def termsofuse
  end

  def privacy
  end

  def example
  end

  def overview
  end

  def home
    @repositories = Arclight::Repository.all
  end
end
