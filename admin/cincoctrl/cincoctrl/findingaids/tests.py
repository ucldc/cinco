from http import HTTPStatus

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect
from django.test import RequestFactory
from django.urls import reverse

from cincoctrl.findingaids.views import home
from cincoctrl.users.models import User
from cincoctrl.users.tests.factories import UserFactory


class TestFindingAidHomeView:
    def test_authenticated(self, user: User, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = UserFactory()
        response = home(request)

        assert response.status_code == HTTPStatus.OK

    def test_not_authenticated(self, user: User, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()
        response = home(request, pk=user.pk)
        login_url = reverse(settings.LOGIN_URL)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == f"{login_url}?next=/fake-url/"
