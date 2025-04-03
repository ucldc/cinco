from pathlib import Path
from unittest import mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from cincoctrl.findingaids.models import ExpressRecord
from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import Language
from cincoctrl.findingaids.models import SupplementaryFile
from cincoctrl.users.models import Repository
from cincoctrl.users.models import User
from cincoctrl.users.models import UserRole

pytestmark = pytest.mark.django_db

CREATED = 302
OK = 200


class TestFindingAidViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create()
        self.repository = Repository.objects.create()
        UserRole.objects.create(user=self.user, repository=self.repository)
        self.client.force_login(self.user)

    def get_test_file(self, filename):
        filepath = f"cincoctrl/findingaids/tests/test_files/{filename}"
        with Path(filepath).open("rb") as file:
            file_content = file.read()
        return SimpleUploadedFile(filename, file_content)

    @mock.patch.object(FindingAid, "queue_index")
    def test_submit_ead(self, index_mock):
        url = reverse("findingaids:submit_ead")
        title = "Title of the EAD"
        ead_file = self.get_test_file("test_ead1.xml")
        data = {
            "repository": self.repository.pk,
            "ead_file": ead_file,
        }
        response = self.client.post(url, data)

        assert response.status_code == CREATED
        assert FindingAid.objects.count() == 1
        assert FindingAid.objects.first().collection_title == title
        index_mock.assert_called_once()

    @mock.patch.object(FindingAid, "queue_index")
    def test_submit_ead_invalid(self, index_mock):
        url = reverse("findingaids:submit_ead")
        data = {
            "repository": self.repository.pk,
        }
        response = self.client.post(url, data)

        assert response.status_code == OK
        assert FindingAid.objects.count() == 0
        index_mock.assert_not_called()

    @mock.patch.object(FindingAid, "queue_index")
    def test_create_recordexpress(self, index_mock):
        url = reverse("findingaids:create_record_express")
        title = "Collection Title"
        data = {
            "repository": self.repository.pk,
            "collection_title": title,
            "collection_number": "test",
            "title_filing": "test",
            "date": "1",
            "extent": "test",
            "abstract": "test",
            "scopecontent": "test",
            "language": Language.objects.create(code="eng", name="English").pk,
            "accessrestrict": "test",
            "revisionhistory_set-TOTAL_FORMS": "1",
            "revisionhistory_set-INITIAL_FORMS": "0",
            "revisionhistory_set-MIN_NUM_FORMS": "0",
            "revisionhistory_set-MAX_NUM_FORMS": "1000",
            "revisionhistory_set-0-note": "",
            "revisionhistory_set-0-id": "",
            "revisionhistory_set-0-record": "",
            "expressrecordcreator_set-TOTAL_FORMS": "1",
            "expressrecordcreator_set-INITIAL_FORMS": "0",
            "expressrecordcreator_set-MIN_NUM_FORMS": "0",
            "expressrecordcreator_set-MAX_NUM_FORMS": "1000",
            "expressrecordcreator_set-0-creator_type": "",
            "expressrecordcreator_set-0-value": "",
            "expressrecordcreator_set-0-id": "",
            "expressrecordcreator_set-0-record": "",
            "expressrecordsubject_set-TOTAL_FORMS": "1",
            "expressrecordsubject_set-INITIAL_FORMS": "0",
            "expressrecordsubject_set-MIN_NUM_FORMS": "0",
            "expressrecordsubject_set-MAX_NUM_FORMS": "1000",
            "expressrecordsubject_set-0-subject_type": "",
            "expressrecordsubject_set-0-value": "",
            "expressrecordsubject_set-0-id": "",
            "expressrecordsubject_set-0-record": "",
        }
        response = self.client.post(url, data)

        assert response.status_code == CREATED
        assert FindingAid.objects.count() == 1
        assert FindingAid.objects.first().collection_title == title
        assert ExpressRecord.objects.count() == 1
        index_mock.assert_called_once()

    @mock.patch.object(FindingAid, "queue_index")
    def test_create_recordexpress_invalid(self, index_mock):
        url = reverse("findingaids:create_record_express")
        data = {
            "title_filing": "test",
            "date": "1",
            "extent": "test",
            "abstract": "test",
            "scopecontent": "test",
            "language": Language.objects.create(code="eng", name="English").pk,
            "accessrestrict": "test",
            "revisionhistory_set-TOTAL_FORMS": "1",
            "revisionhistory_set-INITIAL_FORMS": "0",
            "revisionhistory_set-MIN_NUM_FORMS": "0",
            "revisionhistory_set-MAX_NUM_FORMS": "1000",
            "revisionhistory_set-0-note": "",
            "revisionhistory_set-0-id": "",
            "revisionhistory_set-0-record": "",
            "expressrecordcreator_set-TOTAL_FORMS": "1",
            "expressrecordcreator_set-INITIAL_FORMS": "0",
            "expressrecordcreator_set-MIN_NUM_FORMS": "0",
            "expressrecordcreator_set-MAX_NUM_FORMS": "1000",
            "expressrecordcreator_set-0-creator_type": "",
            "expressrecordcreator_set-0-value": "",
            "expressrecordcreator_set-0-id": "",
            "expressrecordcreator_set-0-record": "",
            "expressrecordsubject_set-TOTAL_FORMS": "1",
            "expressrecordsubject_set-INITIAL_FORMS": "0",
            "expressrecordsubject_set-MIN_NUM_FORMS": "0",
            "expressrecordsubject_set-MAX_NUM_FORMS": "1000",
            "expressrecordsubject_set-0-subject_type": "",
            "expressrecordsubject_set-0-value": "",
            "expressrecordsubject_set-0-id": "",
            "expressrecordsubject_set-0-record": "",
        }
        response = self.client.post(url, data)

        assert response.status_code == OK
        assert FindingAid.objects.count() == 0
        assert ExpressRecord.objects.count() == 0
        index_mock.assert_not_called()

    @mock.patch.object(FindingAid, "queue_index")
    def test_attach_pdf(self, index_mock):
        finding_aid = FindingAid.objects.create(
            repository=self.repository,
            collection_title="Test Collection",
            collection_number="COLL_NUM",
        )
        pdf_file = self.get_test_file("test_pdf.pdf")

        url = reverse("findingaids:attach_pdf", kwargs={"pk": finding_aid.pk})
        data = {
            "supplementaryfile_set-TOTAL_FORMS": "1",
            "supplementaryfile_set-INITIAL_FORMS": "0",
            "supplementaryfile_set-MIN_NUM_FORMS": "0",
            "supplementaryfile_set-MAX_NUM_FORMS": "1000",
            "supplementaryfile_set-0-title": "supp file 1",
            "supplementaryfile_set-0-order": "0",
            "supplementaryfile_set-0-id": "",
            "supplementaryfile_set-0-finding_aid": finding_aid.pk,
            "supplementaryfile_set-0-pdf_file": pdf_file,
        }
        response = self.client.post(url, data)

        assert response.status_code == CREATED
        assert SupplementaryFile.objects.count() == 1
        index_mock.assert_called_once()
