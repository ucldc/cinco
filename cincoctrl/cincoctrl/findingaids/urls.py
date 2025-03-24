from django.urls import path

from cincoctrl.findingaids.views import attach_pdf
from cincoctrl.findingaids.views import create_record_express
from cincoctrl.findingaids.views import language_autocomplete
from cincoctrl.findingaids.views import manage_records_view
from cincoctrl.findingaids.views import preview_record
from cincoctrl.findingaids.views import publish_record
from cincoctrl.findingaids.views import submit_ead
from cincoctrl.findingaids.views import update_ead
from cincoctrl.findingaids.views import update_record_express
from cincoctrl.findingaids.views import view_record
from cincoctrl.findingaids.views import view_record_express_xml

app_name = "findingaids"
urlpatterns = [
    path(
        "language-autocomplete/",
        view=language_autocomplete,
        name="language-autocomplete",
    ),
    path("records/manage/", view=manage_records_view, name="manage_records"),
    path("ead/submit/", view=submit_ead, name="submit_ead"),
    path("ead/<int:pk>/update", view=update_ead, name="update_ead"),
    path(
        "recordexpress/create/",
        view=create_record_express,
        name="create_record_express",
    ),
    path(
        "recordexpress/<int:pk>/",
        view=view_record_express_xml,
        name="view_record_express_xml",
    ),
    path(
        "recordexpress/<int:pk>/update",
        view=update_record_express,
        name="update_record_express",
    ),
    path("records/<int:pk>/", view=view_record, name="view_record"),
    path("records/<int:pk>/published", view=publish_record, name="publish_record"),
    path("records/<int:pk>/previewed", view=preview_record, name="preview_record"),
    path("records/<int:pk>/attach", view=attach_pdf, name="attach_pdf"),
]
