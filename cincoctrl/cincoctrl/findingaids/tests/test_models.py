import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import TestCase

from cincoctrl.findingaids.models import ExpressRecord
from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import Language
from cincoctrl.findingaids.models import ValidationWarning
from cincoctrl.users.models import Repository

INVALID_DTD1 = """
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE ead PUBLIC
    "+//ISBN 1-931666-00-8//DTD ead.dtd
    (Encoded Archival Description (EAD) Version 2002)//EN"
    "ead.dtd">
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
<!DOCTYPE ead PUBLIC
    "+//ISBN 1-931666-00-8//DTD ead.dtd
    (Encoded Archival Description (EAD) Version 2002)//EN"
    "ead.dtd">
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


class TestFindingAidModels(TestCase):
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

    @pytest.mark.django_db
    def test_record_express_template(self):
        repo = Repository.objects.create(
            ark="0000",
            code="repo1",
            name="Repository 1",
        )
        eng = Language.objects.create(code="eng", name="English")
        f = FindingAid.objects.create(
            repository=repo,
            collection_title="Test Collection",
            collection_number="COLL_NUM",
        )
        e = ExpressRecord.objects.create(
            finding_aid=f,
            title_filing="Test Title",
            date="1999",
            extent="Extent of Collection",
            abstract="This is the abstract",
            accessrestrict="Access Restrictions",
            scopecontent="Scope and Content",
        )
        e.language.add(eng)

        record = render_to_string(
            "findingaids/express_record.xml",
            context={"object": e},
        )
        assert '<language langcode="eng"/>' in record
