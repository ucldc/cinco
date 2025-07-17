class ContactMailer < ApplicationMailer
    default from: "oacops@cdlib.org"
    default to: "oac-feedback-l@listserv.ucop.edu"

    def contact_email(message, sender_name, sender_email, sender_verify_email, referrer)
        formatted_message = "Message: #{message}\n\n" \
            "Sender name: #{sender_name}\n\n" \
            "Sender email: #{sender_email}\n\n" \
            "Sender verify email: #{sender_verify_email}\n\n" \
            "Referrer: #{referrer}\n\n"

        mail(
            reply_to: sender_email,
            subject: "[OAC Feedback] #{sender_name} has sent a message",
            body: formatted_message
        )
    end
end
