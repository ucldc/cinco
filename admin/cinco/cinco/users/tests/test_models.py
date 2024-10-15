import pytest

from cinco.users.models import User, Repository, UserRole

@pytest.fixture
def repository():
    return Repository()

def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/users/{user.pk}/"

def test_user_has_repo_access(user: User, repository: Repository):
    assert user.has_repo_access(repository.pk) == False
    UserRole(user=user, repository=repository)
    assert user.has_repo_access(repository.pk)
