import pytest

from cincoctrl.users.models import Repository
from cincoctrl.users.models import User
from cincoctrl.users.models import UserRole


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/users/{user.pk}/"


@pytest.mark.django_db
def test_user_has_repo_access(user: User):
    repository = Repository.objects.create(
        ark="0000",
        code="repo1",
        name="Repository 1",
    )
    assert not user.has_repo_access(repository.code)
    _role = UserRole.objects.create(user=user, repository=repository)
    assert user.has_repo_access(repository.code)
