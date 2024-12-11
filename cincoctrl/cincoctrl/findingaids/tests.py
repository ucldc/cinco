from http import HTTPStatus

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseRedirect
from django.test import RequestFactory
from django.urls import reverse

from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.validators import validate_ead
from cincoctrl.findingaids.views import home
from cincoctrl.users.models import User
from cincoctrl.users.tests.factories import UserFactory

TEST_XML = """
<?xml version="1.0" encoding="utf-8"?>
<ead>
    <eadheader countryencoding="iso3166-1" dateencoding="iso8601"
        langencoding="iso639-2b" repositoryencoding="iso15511">
        <eadid countrycode="US" mainagencycode="repo_code">0000_0000.xml</eadid>
    </eadheader>
    <archdesc level="collection">
        <did>
            <langmaterial>
                <language langcode="eng">English</language>
            </langmaterial>
            <repository>
                <corpname>Test Library</corpname>
            </repository>
            <unittitle>Title of the EAD</unittitle>
            <unitid>0000-0000</unitid>
        </did>
    </archdesc>
</ead>
"""

TEST_INVALID_XML = """
<?xml version="1.0" encoding="utf-8"?>
<ead>
    <eadheader countryencoding="iso3166-1" dateencoding="iso8601"
        langencoding="iso639-2b" repositoryencoding="iso15511">
        <eadid countrycode="US" mainagencycode="repo_code">0000_0000.xml</eadid>
    </eadheader>
    <archdesc level="collection">
        <did>
            <langmaterial>
                <language langcode="eng">English</language>
            </langmaterial>
            <repository>
                <corpname>Test Library</corpname>
            </repository>
            <unittitle>Title of the EAD</unittitle>
            <unitid>0000-0000</unitid>
        </did>
    </archdesc>
"""

TEST_NO_EADID = """
<?xml version="1.0" encoding="utf-8"?>
<ead>
    <eadheader countryencoding="iso3166-1" dateencoding="iso8601"
        langencoding="iso639-2b" repositoryencoding="iso15511">
    </eadheader>
    <archdesc level="collection">
        <did>
            <langmaterial>
                <language langcode="eng">English</language>
            </langmaterial>
            <repository>
                <corpname>Test Library</corpname>
            </repository>
            <unittitle>Title of the EAD</unittitle>
            <unitid>0000-0000</unitid>
        </did>
    </archdesc>
</ead>
"""

TEST_NO_UNITTITLE = """
<?xml version="1.0" encoding="utf-8"?>
<ead>
    <eadheader countryencoding="iso3166-1" dateencoding="iso8601"
        langencoding="iso639-2b" repositoryencoding="iso15511">
        <eadid countrycode="US" mainagencycode="repo_code">0000_0000.xml</eadid>
    </eadheader>
    <archdesc level="collection">
        <did>
            <langmaterial>
                <language langcode="eng">English</language>
            </langmaterial>
            <repository>
                <corpname>Test Library</corpname>
            </repository>
            <unitid>0000-0000</unitid>
        </did>
    </archdesc>
</ead>
"""

TEST_NO_UNITID = """
<?xml version="1.0" encoding="utf-8"?>
<ead>
    <eadheader countryencoding="iso3166-1" dateencoding="iso8601"
        langencoding="iso639-2b" repositoryencoding="iso15511">
        <eadid countrycode="US" mainagencycode="repo_code">0000_0000.xml</eadid>
    </eadheader>
    <archdesc level="collection">
        <did>
            <langmaterial>
                <language langcode="eng">English</language>
            </langmaterial>
            <repository>
                <corpname>Test Library</corpname>
            </repository>
            <unittitle>Title of the EAD</unittitle>
        </did>
    </archdesc>
</ead>
"""


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


class TestFindingAidModels:
    def test_extract_ead(self):
        ead_file = SimpleUploadedFile("test.xml", TEST_XML.strip().encode("utf-8"))
        fa = FindingAid(ead_file=ead_file)
        title, number = fa.extract_ead_fields()
        assert title == "Title of the EAD"
        assert number == "0000-0000"

    def test_validate_ead(self):
        ead_file = SimpleUploadedFile("test.xml", TEST_XML.strip().encode("utf-8"))
        validate_ead(ead_file)

    def test_invalid_xml(self):
        ead_file = SimpleUploadedFile(
            "test.xml",
            TEST_INVALID_XML.strip().encode("utf-8"),
        )
        with pytest.raises(ValidationError) as e:
            validate_ead(ead_file)
        assert "Invalid XML file." in str(e)

    def test_no_eadid(self):
        ead_file = SimpleUploadedFile("test.xml", TEST_NO_EADID.strip().encode("utf-8"))
        with pytest.raises(ValidationError) as e:
            validate_ead(ead_file)
        assert "Invalid EADID" in str(e)

    def test_no_unittitle(self):
        ead_file = SimpleUploadedFile(
            "test.xml",
            TEST_NO_UNITTITLE.strip().encode("utf-8"),
        )
        with pytest.raises(ValidationError) as e:
            validate_ead(ead_file)
        assert "Title not found" in str(e)

    def test_no_unitid(self):
        ead_file = SimpleUploadedFile(
            "test.xml",
            TEST_NO_UNITID.strip().encode("utf-8"),
        )
        with pytest.raises(ValidationError) as e:
            validate_ead(ead_file)
        assert "Collection number not found" in str(e)
