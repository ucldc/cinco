crumb :example do
  link "Example Static Page", example_path
  parent :root
end

crumb :about do
  link "About OAC", about_path
  parent :root
end

crumb :privacy do
  link "Privacy Statement", privacy_path
  parent :root
end

crumb :termsofuse do
  link "Terms of Use", termsofuse_path
  parent :root
end

crumb :help do
  link "FAQs", help_path
  parent :root
end

crumb :overview do
  link "Overview", overview_path
  parent :root
end

crumb :contact do
  link "Contact Us", contact_form_path, data: { turbo: "false" }
  parent :root
end

crumb :quickstart do
  link "Quick Start Guide", quickstart_path
  parent :root
end
