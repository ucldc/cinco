from django.urls import resolve
from django.urls import reverse

from cincoctrl.users.models import User


def test_detail(user: User):
    assert reverse("users:detail", kwargs={"pk": user.pk}) == f"/users/{user.pk}/"
    assert resolve(f"/users/{user.pk}/").view_name == "users:detail"


def test_change_password(user: User):
    assert reverse("users:change_password") == "/users/changepassword/"
    assert resolve("/users/changepassword/").view_name == "users:change_password"


def test_repositories(user: User):
    assert reverse("users:list_repositories") == "/users/repositories/"
    assert resolve("/users/repositories/").view_name == "users:list_repositories"
