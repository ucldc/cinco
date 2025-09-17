class ErrorsController < ApplicationController
    def not_found
        render "errors/not_found", status: :not_found
    end
end
