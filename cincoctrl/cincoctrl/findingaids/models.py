import uuid
import xml.etree.ElementTree as ET

from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import FileField
from django.db.models import ForeignKey
from django.db.models import IntegerField
from django.db.models import OneToOneField
from django.db.models import TextField
from django.db.models import URLField
from django.urls import reverse

from cincoctrl.findingaids.validators import validate_ead

FILE_FORMATS = (
    ("ead", "EAD"),
    ("marc", "MARC"),
)

STATUSES = (
    ("imported", "Imported"),
    ("previewed", "Previewed"),
    ("published", "Published"),
    ("updated", "Updated"),
)

RECORD_TYPES = (
    ("express", "Record Express"),
    ("ead", "EAD"),
    ("ead_pdf", "EAD with PDF"),
)


def get_record_type_label(t):
    for v, n in RECORD_TYPES:
        if t == v:
            return n
    raise ValueError("Invalid record type")


class FindingAid(models.Model):
    ark = CharField(max_length=255, unique=True)  # auto-assigned
    repository = ForeignKey("users.Repository", on_delete=models.CASCADE)  # system-set
    created_by = ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )  # system-set
    collection_title = CharField(max_length=255)  # extracted from ead if present
    collection_number = CharField(max_length=255)  # extracted from ead if present
    ead_file = FileField(
        upload_to="ead/",
        validators=[FileExtensionValidator(["xml"]), validate_ead],
        null=True,
        blank=True,
    )
    record_type = CharField(max_length=10, choices=RECORD_TYPES)  # system-set
    status = CharField(
        max_length=50,
        default="imported",
        choices=STATUSES,
    )  # system-set
    date_created = DateTimeField(auto_now_add=True)  # auto-assigned
    date_updated = DateTimeField(auto_now=True)  # auto-updated

    def __str__(self):
        return self.collection_title

    def save(self, *args, **kwargs):
        if not self.ark:
            self.ark = uuid.uuid4()
        super().save(*args, **kwargs)
        if self.record_type != "express":
            self.collection_title, self.collection_number = self.extract_ead_fields()
            super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        if self.record_type == "express":
            return reverse(
                "findingaids:view_record_express",
                kwargs={"pk": self.expressrecord.pk, "repo_slug": self.repository.code},
            )
        return reverse(
            "findingaids:view_record",
            kwargs={"pk": self.id, "repo_slug": self.repository.code},
        )

    def extract_ead_fields(self):
        with self.ead_file.open("rb") as f:
            root = ET.parse(f).getroot()
        title_node = root.find("./archdesc/did/unittitle")
        number_node = root.find("./archdesc/did/unitid")
        return title_node.text, number_node.text


class SupplementaryFile(models.Model):
    finding_aid = ForeignKey("FindingAid", on_delete=models.CASCADE)
    pdf_file = FileField(upload_to="pdf/", validators=[FileExtensionValidator(["pdf"])])
    date_created = DateTimeField(auto_now_add=True)
    date_updated = DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.finding_aid} / {self.pdf_file}"


class ExpressRecord(models.Model):
    finding_aid = OneToOneField("FindingAid", on_delete=models.CASCADE)
    title_filing = CharField("Collection Title (Filing)", max_length=255)
    date = CharField("Collection Date", max_length=128)
    start_year = IntegerField(null=True, blank=True)
    end_year = IntegerField(null=True, blank=True)
    extent = TextField("Extent of Collection")
    abstract = TextField()
    language = CharField("Language of materials", max_length=3)
    accessrestrict = TextField("Access Conditions")
    userestrict = TextField("Publication Rights", blank=True)
    acqinfo = TextField("Acquisition Information", blank=True)
    scopecontent = TextField("Scope and Content of Collection")
    bioghist = TextField("Biography/Administrative History", blank=True)
    online_items_url = URLField("Online Items URL", blank=True)
    author_statement = TextField(blank=True)
    preferred_citation = TextField(blank=True)
    processing_information = TextField(blank=True)
    date_created = DateTimeField(auto_now_add=True)
    date_updated = DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.finding_aid} (Express)"

    def get_absolute_url(self) -> str:
        return reverse(
            "findingaids:view_record_express",
            kwargs={"pk": self.pk, "repo_slug": self.finding_aid.repository.code},
        )


CREATOR_TYPES = (
    ("persname", "Person"),
    ("famname", "Family"),
    ("corpname", "Organization"),
)


class ExpressRecordCreator(models.Model):
    record = ForeignKey("ExpressRecord", on_delete=models.CASCADE)
    creator_type = CharField(max_length=10, choices=CREATOR_TYPES)
    value = TextField()

    def __str__(self):
        return f"Creator {self.creator_type} = {self.value}"


SUBJECT_TYPES = (
    ("subject", "Topic"),
    ("persname", "Person"),
    ("famname", "Family"),
    ("corpname", "Organization"),
    ("geogname", "Geographic coverage"),
    ("genreform", "Genre"),
    ("title", "Title"),
    ("function", "Function"),
    ("occupation", "Occupation"),
)


class ExpressRecordSubject(models.Model):
    record = ForeignKey("ExpressRecord", on_delete=models.CASCADE)
    subject_type = CharField(max_length=10, choices=SUBJECT_TYPES)
    value = TextField()

    def __str__(self):
        return f"Subject {self.subject_type} = {self.value}"


class RevisionHistory(models.Model):
    record = ForeignKey("ExpressRecord", on_delete=models.CASCADE)
    date_revised = DateTimeField(auto_now_add=True)
    note = TextField("Revision Note")

    def __str__(self):
        return f"{self.date_revised}: {self.note}"
