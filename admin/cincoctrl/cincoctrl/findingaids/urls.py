from django.urls import path

from cincoctrl.findingaids.views import home
from cincoctrl.findingaids.views import list_records
from cincoctrl.findingaids.views import update_record
from cincoctrl.findingaids.views import upload_ead
from cincoctrl.findingaids.views import view_record

app_name = "findingaids"
urlpatterns = [
    path("", view=home, name="home"),
    path("records/<int:record_id>/", view=view_record, name="view_record"),
    path(
        "records/<int:repository_id>/<str:record_type>/",
        view=list_records,
        name="list_records",
    ),
    path("records/<int:repository_id>/ead/upload/", view=upload_ead, name="upload_ead"),
    path("records/<int:record_id>/update", view=update_record, name="update_record"),
]
