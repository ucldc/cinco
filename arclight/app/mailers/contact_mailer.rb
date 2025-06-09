class ContactMailer < ApplicationMailer
    default from: "oac-feedback-l@ucop.edu"
    #default to: "oac-feedback-l@listserv.ucop.edu"
    default to: "barbara.hui@ucop.edu"

    def contact_email(subject, message, user_category, user_category_other_description, sender_name, sender_email)
        formatted_message = "Subject: #{subject}\n\n" \
            "Message: #{message}\n\n" \
            "User category: #{user_category}\n\n" \
            "Other description: #{user_category_other_description}\n\n" \
            "Sender name: #{sender_name}\n\n" \
            "Sender email: #{sender_email}\n\n"

        mail(
            reply_to: sender_email,
            subject: subject,
            body: formatted_message
        )
    end
end
