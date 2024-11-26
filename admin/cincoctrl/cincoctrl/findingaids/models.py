from django.db import models
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import FileField
from django.db.models import ForeignKey
from django.db.models import TextField
from django.db.models import URLField

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

FIELD_TERMS = (
    ("CR", "Creator"),
    ("SU", "Subject"),
    ("CVR", "Coverage"),
    ("TY", "Type"),
)

FIELD_QUALIFIERS = (
    ("P", "Person"),
    ("F", "Family"),
    ("O", "Organization"),
    ("T", "Topic"),
    ("GEO", "Geography"),
    ("GN", "Genre"),
    ("TI", "Title"),
    ("OC", "Occupation"),
)


class FindingAid(models.Model):
    ark = CharField(max_length=255, unique=True)  # auto-assigned
    repository = ForeignKey("users.Repository", on_delete=models.CASCADE)  # auto
    created_by = ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )  # auto
    collection_title = CharField(max_length=255)  # extracted
    collection_number = CharField(max_length=255)  # extracted
    ead_file = ForeignKey("File", on_delete=models.CASCADE)  # user select
    record_type = CharField(max_length=10, choices=RECORD_TYPES)  # auto
    status = CharField(max_length=50, default="imported", choices=STATUSES)  # auto
    date_created = DateTimeField(auto_now_add=True)  # auto
    date_updated = DateTimeField(auto_now=True)  # auto

    def __str__(self):
        return self.collection_title


class SupplementaryFile(models.Model):
    finding_aid = ForeignKey("FindingAid", on_delete=models.CASCADE)
    file = ForeignKey("File", on_delete=models.CASCADE)
    date_created = DateTimeField(auto_now_add=True)
    date_updated = DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.finding_aid} / {self.file}"


class File(models.Model):
    file = FileField()

    def __str__(self):
        return f"{self.file}"


class ExpressRecord(models.Model):
    finding_aid = ForeignKey("FindingAid", on_delete=models.CASCADE)
    title_filing = CharField("Collection Title (Filing)", max_length=255)
    local_identifier = CharField("Collection Identifier/Call Number", max_length=255)
    date_dacs = CharField("Collection Date", max_length=128)
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


class ExpressRecordField(models.Model):
    record = ForeignKey("ExpressRecord", on_delete=models.CASCADE)
    term = CharField(max_length=5, choices=FIELD_TERMS)
    qualifier = CharField(max_length=5, choices=FIELD_QUALIFIERS)
    value = TextField()

    def __str__(self):
        return f"{self.term} / {self.qualifier} = {self.value}"


class RevisionHistory(models.Model):
    record = ForeignKey("ExpressRecord", on_delete=models.CASCADE)
    date_revised = DateTimeField(auto_now_add=True)
    note = TextField()

    def __str__(self):
        return f"{self.date_revised}: {self.note}"
