class ContactMailer < ApplicationMailer
    default from: "oac-feedback-l@ucop.edu"
    default to: "oac-feedback-l@listserv.ucop.edu"

    def test(email)
        mail(reply_to: email, subject: "Hello World!")
    end
end
