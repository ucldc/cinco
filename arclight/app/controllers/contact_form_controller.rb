class ContactFormController < ApplicationController
    def create
        @subject = params[:contact_form][:subject]
        @message = params[:contact_form][:message]
        @user_category = params[:contact_form][:user_category]
        @user_category_other_description = params[:contact_form][:user_category_other_description]
        @sender_name = params[:contact_form][:sender_name]
        @sender_email = params[:contact_form][:sender_email]

        ContactMailer.contact_email(@subject, @message, @user_category, @user_category_other_description, @sender_name, @sender_email).deliver_now
        flash[:success] = "Your message has been sent successfully."
        redirect_to :root
    end
end
