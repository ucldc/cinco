import re

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.parser import EADParser
from cincoctrl.findingaids.validators import validate_ead

OTHER1 = """
<ead xmlns:xlink="http://www.w3.org/1999/xlink"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="urn:isbn:1-931666-22-9
     http://www.loc.gov/ead/ead.xsd">
    <eadheader countryencoding="iso3166-1" dateencoding="iso8601"
        langencoding="iso639-2b" repositoryencoding="iso15511">
        <eadid xmlns:cdlpath="http://www.cdlib.org/path/"
               countrycode="us"
               identifier="ark:/00000/a00000a0bb"
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

INVALID_NO_DTD = """
<?xml version="1.0" encoding="utf-8"?>
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

COLLECTION_LEVEL = """
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
        <dsc type="combined" id="dsc-1.2.10" score="0" C-ORDER="1" MAX-C-ORDER="1">
            <c01 id="aspace_ref1_1aa" level="collection" score="1" C-ORDER="1">
                <did>
                    <unittitle>Papers</unittitle>
                    <unitdate datechar="creation">1908-1926</unitdate>
                    <physdesc id="aspace_1" label="Description note">(1 box)</physdesc>
                </did>
            </c01>
        </dsc>
    </archdesc>
</ead>
"""

EMPTY_FIELDS = """
<ead>
    <eadheader countryencoding="iso3166-1" dateencoding="iso8601"
        langencoding="iso639-2b" repositoryencoding="iso15511">
        <eadid countrycode="US" mainagencycode="repo_code"></eadid>
    </eadheader>
    <archdesc level="collection">
        <did>
            <langmaterial>
                <language langcode="eng">English</language>
            </langmaterial>
            <repository>
                <corpname>Test Library</corpname>
            </repository>
            <unittitle></unittitle>
            <unitid></unitid>
        </did>
    </archdesc>
</ead>
"""


class TestParser(TestCase):
    def get_ead_file(self, filename, xml_str):
        return SimpleUploadedFile(filename, xml_str.strip().encode("utf-8"))

    def test_extract_ead(self):
        ead_file = self.get_ead_file("test.xml", TEST_XML)
        fa = FindingAid(ead_file=ead_file)
        title, number, ark = fa.extract_ead_fields()
        assert title == "Title of the EAD"
        assert number == "0000-0000"
        assert ark is None

    def test_validate_ead(self):
        ead_file = self.get_ead_file("test.xml", TEST_XML)
        validate_ead(ead_file)

    def test_invalid_xml(self):
        ead_file = self.get_ead_file("test.xml", TEST_INVALID_XML)
        with pytest.raises(ValidationError) as e:
            validate_ead(ead_file)
        assert "Could not parse XML file:" in str(e)

    def test_no_unittitle(self):
        ead_file = self.get_ead_file("test.xml", TEST_NO_UNITTITLE)
        with pytest.raises(ValidationError) as e:
            validate_ead(ead_file)
        assert "Failed to parse Title" in str(e)

    def test_no_unitid(self):
        ead_file = self.get_ead_file("test.xml", TEST_NO_UNITID)
        with pytest.raises(ValidationError) as e:
            validate_ead(ead_file)
        assert "Failed to parse Collection number" in str(e)

    def test_invalid_no_dtd(self):
        ead_file = self.get_ead_file("test.xml", INVALID_NO_DTD)
        p = EADParser()
        p.parse_file(ead_file)
        p.validate_dtd()
        assert len(p.warnings) == 0

    def test_no_comp_title(self):
        p = EADParser()
        p.parse_string(NO_COMP_TITLE)
        p.validate_component_titles()
        assert len(p.warnings) == 1
        assert p.warnings[0] == "No title for non-empty component: x311358872"

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
        ark = p.parse_ark()
        parent_ark = p.parse_parent_ark()
        assert ark == "ark:/00000/a00000a0bb"
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

    def test_invalid_collection_level(self):
        p = EADParser()
        p.parse_string(COLLECTION_LEVEL)
        p.validate_component_titles()
        assert len(p.warnings) == 1
        assert (
            p.warnings[0] == "Components cannot have level=collection: aspace_ref1_1aa"
        )

    def test_empty_required_fields(self):
        p = EADParser()
        p.parse_string(EMPTY_FIELDS)
        p.validate_required_fields()
        assert len(p.errors) == 2  # noqa: PLR2004
        assert p.errors[0] == "No value in Title"
        assert p.errors[1] == "No value in Collection number"
