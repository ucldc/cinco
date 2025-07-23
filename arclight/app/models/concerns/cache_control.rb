module CacheControl
  extend ActiveSupport::Concern

  included do
    before_action only: [ :index, :show ] do
      expires_in 7.days, public: true
    end
  end
end
