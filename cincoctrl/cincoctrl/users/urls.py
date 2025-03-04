from django.urls import path

from .views import repository_list_view
from .views import user_change_password
from .views import user_detail_view

app_name = "users"
urlpatterns = [
    path("<int:pk>/", view=user_detail_view, name="detail"),
    path("<int:pk>/changepassword/", view=user_change_password, name="change_password"),
    path("repositories/", view=repository_list_view, name="list_repositories"),
]
