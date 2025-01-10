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
from cincoctrl.findingaids.parser import EADParser
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

INVALID_DTD = """
<record>
    <title>This is not EAD</title>
</record>
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

NO_COMP_TITLE = """
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
        <dsc type="combined">
            <c01 level="series" id="x311358872">
                <did>
                </did>
                <c02 level="item" id="m31133255">
                    <did>
                        <unittitle>Component 2 Title</unittitle>
                    </did>
                </c02>
            </c01>
        </dsc>
    </archdesc>
</ead>
"""

INVALID_DATERANGE = """
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
        <dsc type="combined">
            <c01 level="series" id="x311358872">
                <did>
                    <unittitle>Component 1 Title</unittitle>
                </did>
                <c02 level="item" id="m31133255">
                    <did>
                        <unittitle>Component 2 Title</unittitle>
                        <unitdate normal="1869/70">1869-70</unitdate>
                    </did>
                </c02>
            </c01>
        </dsc>
    </archdesc>
</ead>
"""

INVALID_DATEFORMAT = """
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
        <dsc type="combined">
            <c01 level="series" id="x311358872">
                <did>
                    <unittitle>Component 1 Title</unittitle>
                </did>
                <c02 level="item" id="m31133255">
                    <did>
                        <unittitle>Component 2 Title</unittitle>
                        <unitdate normal="29/10/1869">[October 29 1869?]</unitdate>
                    </did>
                </c02>
            </c01>
        </dsc>
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
        assert "Could not parse XML file:" in str(e)

    def test_no_eadid(self):
        ead_file = SimpleUploadedFile("test.xml", TEST_NO_EADID.strip().encode("utf-8"))
        with pytest.raises(ValidationError) as e:
            validate_ead(ead_file)
        assert "Failed to parse EADID" in str(e)

    def test_no_unittitle(self):
        ead_file = SimpleUploadedFile(
            "test.xml",
            TEST_NO_UNITTITLE.strip().encode("utf-8"),
        )
        with pytest.raises(ValidationError) as e:
            validate_ead(ead_file)
        assert "Failed to parse Title" in str(e)

    def test_no_unitid(self):
        ead_file = SimpleUploadedFile(
            "test.xml",
            TEST_NO_UNITID.strip().encode("utf-8"),
        )
        with pytest.raises(ValidationError) as e:
            validate_ead(ead_file)
        assert "Failed to parse Collection number" in str(e)

    def test_invalid_dtd(self):
        p = EADParser()
        p.parse_string(INVALID_DTD)
        p.validate_dtd()
        assert len(p.warnings) == 1
        assert (
            p.warnings[0] == "Could not validate dtd: No declaration for element record"
        )

    def test_no_comp_title(self):
        p = EADParser()
        p.parse_string(NO_COMP_TITLE)
        p.validate_component_titles()
        assert len(p.errors) == 1
        assert p.errors[0] == "No title for non-empty component: x311358872"

    def test_bad_date_range(self):
        p = EADParser()
        p.parse_string(INVALID_DATERANGE)
        p.validate_dates()
        assert len(p.warnings) == 1
        assert p.warnings[0] == "End year (70) before start year (1869)"

    def test_invalid_dateformat(self):
        p = EADParser()
        p.parse_string(INVALID_DATEFORMAT)
        p.validate_dates()
        assert len(p.warnings) == 1
        assert p.warnings[0] == "Invalid date format 29/10/1869"
