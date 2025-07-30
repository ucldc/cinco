module CacheControl
  extend ActiveSupport::Concern

  included do
    before_action only: [ :index, :show, :hierarchy ] do
      expires_in 7.days, public: true
    end
  end
end
