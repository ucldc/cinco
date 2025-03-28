import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import FileField
from django.db.models import ForeignKey
from django.db.models import IntegerField
from django.db.models import ManyToManyField
from django.db.models import OneToOneField
from django.db.models import TextField
from django.db.models import URLField
from django.urls import reverse

from cincoctrl.findingaids.parser import EADParser
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

INDEXING_STATUSES = (
    ("success", "Success"),
    ("failed", "Failed"),
)

RECORD_TYPES = (
    ("express", "Record Express"),
    ("ead", "EAD"),
)

TEXTRACT_STATUSES = (
    ("SUCCEEDED", "Succeeded"),
    ("FAILED", "Failed"),
    ("ERROR", "Error"),
    ("IN_PROGRESS", "In Progress"),
)


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
            self.ark = str(uuid.uuid4())
        super().save(*args, **kwargs)
        if self.record_type != "express" and self.ead_file.name:
            self.collection_title, self.collection_number = self.extract_ead_fields()
            kwargs.update({"force_insert": False})
            super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse(
            "findingaids:view_record",
            kwargs={"pk": self.pk},
        )

    def record_type_label(self):
        return "RecordEXPRESS" if self.record_type == "express" else "EAD"

    def extract_ead_fields(self):
        with self.ead_file.open("rb") as f:
            p = EADParser()
            p.parse_file(f)
        return p.extract_ead_fields()

    def public_url(self):
        return f"{settings.ARCLIGHT_URL}{self.ark}"


class IndexingHistory(models.Model):
    finding_aid = ForeignKey("FindingAid", on_delete=models.CASCADE)
    date = DateTimeField(auto_now_add=True)
    status = CharField(
        max_length=10,
        choices=INDEXING_STATUSES,
        blank=True,
    )  # system set
    message = CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        s = f"Indexing {self.status} on {self.date.strftime("%Y-%m-%d %H:%M:%S")}"
        if len(self.message):
            s += f": {self.message}"
        return s


class SupplementaryFile(models.Model):
    finding_aid = ForeignKey("FindingAid", on_delete=models.CASCADE)
    title = CharField("Title", max_length=255)
    pdf_file = FileField(upload_to="pdf/", validators=[FileExtensionValidator(["pdf"])])
    order = IntegerField("Display sequence")
    date_created = DateTimeField(auto_now_add=True)
    date_updated = DateTimeField(auto_now=True)
    textract_status = CharField(
        max_length=50,
        default="IN_PROGRESS",
        choices=TEXTRACT_STATUSES,
    )
    textract_output = CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["order", "pk"]

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
    language = ManyToManyField("Language", blank=True)
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
            "findingaids:view_record",
            kwargs={"pk": self.finding_aid.pk},
        )


CREATOR_TYPES = (
    ("persname", "Person"),
    ("famname", "Family"),
    ("corpname", "Organization"),
)


class Language(models.Model):
    code = CharField(max_length=3)
    name = CharField(max_length=255)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


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


class ValidationWarning(models.Model):
    finding_aid = ForeignKey("FindingAid", on_delete=models.CASCADE)
    message = CharField(max_length=255)

    def __str__(self):
        return f"{self.finding_aid}: {self.message}"
