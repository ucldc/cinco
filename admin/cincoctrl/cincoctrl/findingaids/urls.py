from django.urls import path

from cincoctrl.findingaids.views import create_record_express
from cincoctrl.findingaids.views import home
from cincoctrl.findingaids.views import record_list_view
from cincoctrl.findingaids.views import update_record
from cincoctrl.findingaids.views import update_record_express
from cincoctrl.findingaids.views import upload_record
from cincoctrl.findingaids.views import view_record
from cincoctrl.findingaids.views import view_record_express
from cincoctrl.findingaids.views import view_record_express_xml

app_name = "findingaids"
urlpatterns = [
    path("records/<str:repo_slug>/<int:pk>/", view=view_record, name="view_record"),
    path("", view=home, name="home"),
    path(
        "records/<str:repo_slug>/<str:record_type>/",
        view=record_list_view,
        name="list_records",
    ),
    path(
        "records/<str:repo_slug>/<str:record_type>/upload/",
        view=upload_record,
        name="upload_record",
    ),
    path(
        "records/<str:repo_slug>/update/<int:pk>/",
        view=update_record,
        name="update_record",
    ),
    path(
        "records/<str:repo_slug>/express/<int:pk>/",
        view=view_record_express,
        name="view_record_express",
    ),
    path(
        "records/<str:repo_slug>/express/create/",
        view=create_record_express,
        name="create_record_express",
    ),
    path(
        "records/<str:repo_slug>/express/update/<int:pk>/",
        view=update_record_express,
        name="update_record_express",
    ),
    path(
        "records/<str:repo_slug>/express/<int:pk>/xml/",
        view=view_record_express_xml,
        name="view_record_express_xml",
    ),
]
