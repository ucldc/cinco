import logging
import urllib.request as urlreq
import uuid
from pathlib import Path
from urllib.parse import urljoin

from django.conf import settings
from django.core.files.base import ContentFile
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

from cincoctrl.airflow_client.mwaa_api_client import trigger_dag
from cincoctrl.findingaids.parser import EADParser
from cincoctrl.findingaids.validators import validate_ead

logger = logging.getLogger(__name__)

FILE_FORMATS = (
    ("ead", "EAD"),
    ("marc", "MARC"),
)

STATUSES = (
    ("started", "Started"),
    ("queued_preview", "Queued for Preview"),
    ("previewed", "Previewed"),
    ("preview_error", "Preview Error"),
    ("queued_publish", "Queued for Publication"),
    ("published", "Published"),
    ("publish_error", "Publication Error"),
    ("unpublished", "Unpublished"),
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
        default="started",
        choices=STATUSES,
    )  # system-set
    ead_filesize = IntegerField(null=True, blank=True)  # auto-assigned
    date_created = DateTimeField(auto_now_add=True)  # auto-assigned
    date_updated = DateTimeField(auto_now=True)  # auto-updated

    class Meta:
        ordering = ["collection_title"]

    def __str__(self):
        return self.collection_title

    def save(self, *args, **kwargs):
        # if updating, override ark found in EAD file with
        # the current value of ark in the database
        if self.pk is not None:
            self.ark = FindingAid.objects.get(id=self.pk).ark
        # mint a new CDL ark
        if not self.ark or not self.ark.startswith(f"ark:/{settings.CDL_ARK_NAAN}/"):
            if settings.DISABLE_ARK_MINTING:
                self.ark = str(uuid.uuid4())
            else:
                self.ark = self.mint_cdl_ark()
        if self.ead_file and self.ead_file.size:
            self.ead_filesize = self.ead_file.size

        super().save(*args, **kwargs)

    def mint_cdl_ark(self):
        ark = None

        # mint a new ARK
        path = f"shoulder/ark:/{settings.CDL_ARK_NAAN}/{settings.CDL_ARK_SHOULDER}"
        response = self.post_to_ezid(path)
        if response.startswith("success:"):
            ark = response.split("success: ")[1]
            logger.info("Minted new ARK: %s", ark)
        else:
            msg = f"ARK minting request failed for path {path}: {response}"
            logger.error(msg)
            raise self.EzidApiError(msg)

        # update the new ezid record with target url, owner
        if ark:
            path = f"/id/{ark}"
            target_url = f"https://www.oac.cdlib.org/findaid/{ark}"
            owner = "cdldsc"
            data = f"_target: {target_url}\n_owner: {owner}"
            response = self.post_to_ezid(path, data)
            if response.startswith("success:"):
                logger.info("Updated ARK: %s", ark)
            else:
                msg = (
                    f"ARK update request failed for path `{path}`"
                    f"with data `{data}`"
                    f"Response was: {response}"
                )
                logger.error(msg)
                raise self.EzidApiError(msg)

        return ark

    class EzidHTTPErrorProcessor(urlreq.HTTPErrorProcessor):
        """Error Processor, required to let 201 responses pass"""

        def http_response(self, request, response):
            if response.code == 201:  # noqa: PLR2004
                my_return = response
            else:
                my_return = urlreq.HTTPErrorProcessor.http_response(
                    self,
                    request,
                    response,
                )
            return my_return

        https_response = http_response

    class EzidApiError(Exception):
        """EZID API error"""

    def post_to_ezid(self, path, data=None):
        opener = urlreq.build_opener(self.EzidHTTPErrorProcessor())
        ezid_handler = urlreq.HTTPBasicAuthHandler()
        ezid_handler.add_password(
            "EZID",
            settings.EZID_ENDPOINT,
            settings.EZID_USERNAME,
            settings.EZID_PASSWORD,
        )
        opener.add_handler(ezid_handler)

        url = urljoin(settings.EZID_ENDPOINT, path)
        request = urlreq.Request(url)  # noqa: S310
        request.get_method = lambda: "POST"
        if data:
            request.add_header("Content-Type", "text/plain; charset=UTF-8")
            request.data = data.encode("UTF-8")

        try:
            connection = opener.open(request)
            return connection.read().decode("UTF-8")
        except urlreq.HTTPError as ezid_error:
            if ezid_error.fp is not None:
                response = ezid_error.fp.read().decode("utf-8")
                if not response.endswith("\n"):
                    response += "\n"
            return response

    def get_absolute_url(self) -> str:  # noqa: DJ012
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
        return f"{settings.ARCLIGHT_URL}/findaid/{self.ark}"

    @property
    def eadid(self):
        if self.ead_file:
            return Path(self.ead_file.name).name
        return self.collection_number

    def update_ead_with_supplementary_files(self) -> bool:
        if not self.ead_file.name:
            return False

        with self.ead_file.open("rb") as file:
            parser = EADParser()
            parser.parse_file(file)

        supplementary_files = [
            (sf.title, sf.pdf_file.url) for sf in self.supplementaryfile_set.all()
        ]
        ead_file_otherfindaids = [
            (ofa["text"], ofa["href"]) for ofa in parser.parse_otherfindaids()
        ]
        additional_files = set(supplementary_files) - set(ead_file_otherfindaids)

        if additional_files:
            parser.update_otherfindaids(
                [{"text": text, "url": href} for text, href in additional_files],
            )

            filename_prefix = self.ead_file.field.upload_to
            if self.ead_file.name.startswith(filename_prefix):
                filename = self.ead_file.name[len(filename_prefix) :]
            else:
                filename = self.ead_file.name

            self.ead_file = ContentFile(
                parser.to_string(),
                name=filename,
            )
            self.save()
            return True

        return False

    def queue_status(self, *, force_publish=False):
        if force_publish or "publish" in self.status:
            self.status = "queued_publish"
            action = "publish"
        else:
            self.status = "queued_preview"
            action = "preview"
        self.save()

        logger.info("update status for %s: %s", self.ark, self.status)
        return action

    def queue_index(self, *, force_publish=False):
        if self.repository.auto_index:
            action = self.queue_status(force_publish=force_publish)
            logger.info("queue index for %s: %s", self.ark, action)

            if settings.ENABLE_AIRFLOW:
                ark_name = self.ark.replace("/", ":")
                trigger_dag(
                    "index_finding_aid",
                    {
                        "finding_aid_id": self.id,
                        "repository_code": self.repository.code,
                        "finding_aid_ark": self.ark,
                        "eadid": self.eadid,
                        "preview": action,
                        "cinco_environment": settings.CINCO_ENVIRONMENT,
                    },
                    dag_note=(
                        f"Indexing {self.ark} from {self.repository.name} "
                        f"({self.repository.code})"
                    ),
                    related_models=[self],
                    dag_run_prefix=f"{settings.AIRFLOW_PROJECT_NAME}__{ark_name}",
                )


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
    language = ManyToManyField("Language")
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

    def normal_date(self):
        if self.start_year and self.end_year:
            return f"{self.start_year}/{self.end_year}"
        return self.start_year


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
