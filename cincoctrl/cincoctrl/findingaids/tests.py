import re

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.signals import post_save
from django.test import TestCase

from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import ValidationWarning
from cincoctrl.findingaids.models import start_indexing_job
from cincoctrl.findingaids.parser import EADParser
from cincoctrl.findingaids.validators import validate_ead
from cincoctrl.users.models import Repository

OTHER1 = """
<ead xmlns:xlink="http://www.w3.org/1999/xlink"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="urn:isbn:1-931666-22-9
     http://www.loc.gov/ead/ead.xsd">
    <eadheader countryencoding="iso3166-1" dateencoding="iso8601"
        langencoding="iso639-2b" repositoryencoding="iso15511">
        <eadid xmlns:cdlpath="http://www.cdlib.org/path/"
               countrycode="us"
               identifier="ark:/00000/a00000a0"
               mainagencycode="repo_code"
               publicid="0000_0000"
               cdlpath:parent="ark:/00000/aa0a00000a">
            0000_0000.xml
        </eadid>
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
        <otherfindaid id="comp_id_otherfindaid">
            <head>Additional Collection Guide</head>
            <p>
                All items from this collection are available in this
                <extref xlink:href="original.pdf" xlink:role="http://oac.cdlib.org/arcrole/supplemental">
                    Original Title
                </extref>
                document.
            </p>
        </otherfindaid>
    </archdesc>
</ead>
"""

OTHER2 = """
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
        <otherfindaid id="otherfindaid">
            <head>Additional collection guides</head>
            <list>
                <item>
                    <extref href="/data/00000/00/a0a00a01/files/original.pdf">
                        Original Title
                    </extref>
                </item>
            </list>
        </otherfindaid>
    </archdesc>
</ead>
"""

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

INVALID_DTD1 = """
<?xml version="1.0" encoding="utf-8"?>
<record>
    <eadheader countryencoding="iso3166-1" dateencoding="iso8601"
        langencoding="iso639-2b" repositoryencoding="iso15511">
        <eadid countrycode="US" mainagencycode="repo_code">0000_0001.xml</eadid>
    </eadheader>
    <archdesc level="collection">
        <did>
            <langmaterial>
                <language langcode="eng">English</language>
            </langmaterial>
            <repository>
                <corpname>Test Library</corpname>
            </repository>
            <unittitle>Title of the EAD 1</unittitle>
            <unitid>0000-0001</unitid>
        </did>
    </archdesc>
</record>
"""

INVALID_DTD2 = """
<?xml version="1.0" encoding="utf-8"?>
<ead>
    <eadheader>
        <eadid countrycode="US" mainagencycode="repo_code">0000_0001.xml</eadid>
        <filedesc>
            <titlestmt>
                <titleproper type="filing">Title</titleproper>
            </titlestmt>
        </filedesc>
    </eadheader>
    <archdesc level="collection">
        <did>
            <langmaterial>
                <language langcode="eng">English</language>
            </langmaterial>
            <repository>
                <corpname>Test Library</corpname>
            </repository>
            <unittitle>Title of the EAD 2</unittitle>
            <unitid>0000-0001</unitid>
        </did>
    </archdesc>
</ead>

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
XML_COMMENTS = """
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
                    </did>
                </c02>
                <!-- <c02 id="c02-1.1.1.1.1.1.1" level="file">-->
            </c01>
        </dsc>
    </archdesc>
</ead>
"""


class TestFindingAidModels(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        post_save.disconnect(start_indexing_job)

    @classmethod
    def tearDownClass(cls):
        post_save.connect(start_indexing_job)
        super().tearDownClass()

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

    def test_xml_comments(self):
        p = EADParser()
        p.parse_string(XML_COMMENTS)
        p.validate_component_titles()
        assert len(p.errors) == 0
        assert len(p.warnings) == 0

    def test_parse_arks(self):
        p = EADParser()
        p.parse_string(OTHER1)
        ark, parent_ark = p.parse_arks()
        assert ark == "ark:/00000/a00000a0"
        assert parent_ark == "ark:/00000/aa0a00000a"

    def test_parse_otherfindaids1(self):
        p = EADParser()
        p.parse_string(OTHER1)
        others = p.parse_otherfindaids()
        assert len(others) == 1
        assert others[0]["href"] == "original.pdf"
        assert others[0]["text"] == "Original Title"

    def test_parse_otherfindaids2(self):
        p = EADParser()
        p.parse_string(OTHER2)
        others = p.parse_otherfindaids()
        assert len(others) == 1
        assert others[0]["href"] == "/data/00000/00/a0a00a01/files/original.pdf"
        assert others[0]["text"] == "Original Title"

    def test_update_otherfindaids1(self):
        p = EADParser()
        p.parse_string(OTHER1)
        urls = [{"url": "https://pdf.test/AAAAAAAA.pdf", "text": "Title 1"}]
        p.update_otherfindaids(urls)
        out = p.to_string().decode("utf-8")
        result = (
            '<list><item><extref href="https://pdf.test/AAAAAAAA.pdf">'
            "Title 1</extref></item></list></otherfindaid>"
        )
        assert result in out

    def test_update_otherfindaids2(self):
        p = EADParser()
        p.parse_string(OTHER2)
        urls = [{"url": "https://pdf.test/AAAAAAAA.pdf", "text": "Original Title"}]
        p.update_otherfindaids(urls)
        out = p.to_string().decode("utf-8")
        out = re.sub(r"\s+", " ", out)
        result = (
            '<list> <item><extref href="https://pdf.test/AAAAAAAA.pdf">'
            "Original Title</extref></item></list>"
        )
        assert result in out

    @pytest.mark.django_db
    def test_validation_warnings(self):
        repository = Repository.objects.create(
            ark="0000",
            code="repo1",
            name="Repository 1",
        )

        ead_file1 = SimpleUploadedFile(
            "invalid.xml",
            INVALID_DTD1.strip().encode("utf-8"),
        )
        fa = FindingAid.objects.create(repository=repository)
        fa.ead_file = ead_file1
        fa.save()
        warnings = ValidationWarning.objects.filter(finding_aid=fa)
        assert warnings.count() == 2  # noqa: PLR2004
        msgs = warnings.values_list("message", flat=True)
        assert "Could not validate dtd: No declaration for element record" in msgs
        m = (
            "Element eadheader content does not follow the DTD "
            "- missing required elements filedesc"
        )
        assert m in msgs

        ead_file2 = SimpleUploadedFile(
            "invalid2.xml",
            INVALID_DTD2.strip().encode("utf-8"),
        )
        fa.ead_file = ead_file2
        fa.save()
        warnings = ValidationWarning.objects.filter(finding_aid=fa)
        assert warnings.count() == 0
