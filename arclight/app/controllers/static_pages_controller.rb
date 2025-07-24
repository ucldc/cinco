class StaticPagesController < ApplicationController
  before_action :set_expiry

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

  def set_expiry
    expires_in 7.days, public: true
  end
end
