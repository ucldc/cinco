class ContactFormController < ApplicationController
    def create
        @message = params[:contact_form][:message]
        @sender_name = params[:contact_form][:sender_name]
        @sender_email = params[:contact_form][:sender_email]
        @sender_verify_email = params[:contact_form][:sender_verify_email]
        @referrer = params[:contact_form][:referrer]
        if @referrer.blank?
            @referrer = "No referrer"
        end

        ContactMailer.contact_email(@message, @sender_name, @sender_email, @sender_verify_email, @referrer).deliver_now
        flash[:success] = "Your message has been sent successfully."
        redirect_to :root
    end
end
