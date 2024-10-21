from django.urls import path

from cincoctrl.findingaids.views import *

app_name = "findingaids"
urlpatterns = [
    path("", view=home, name="home"),
    path("records/<int:record_id>/", view=view_record, name="view_record"),
    path("records/<int:repository_id>/<str:record_type>/", view=list_records, name="list_records"),
    path("records/<int:repository_id>/ead/upload/", view=upload_ead, name="upload_ead"),
    path("records/<int:record_id>/update", view=update_record, name="update_record"),
    # # path("~/records/<int:repository_id>/eadpdf/upload/", view=upload_ead, name="upload_eadpdf"),
    # # path("~/records/eadpdf/<int:record_id>/", view=update_ead, name="update_eadpdf"),
    # path("records/<int:repository_id>/recordexpress/create/", view=create_record_express, name="create_record_express"),
    # path("records/recordexpress/<int:record_id>/edit/", view=edit_record_express, name="edit_record_express"),
    # path("records/recordexpress/<int:record_id>/xml/", view=viewxml_record_express, name="viewxml_record_express"),
]
