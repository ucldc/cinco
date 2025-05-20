from tempfile import TemporaryFile

from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.template.loader import render_to_string

from cincoctrl.findingaids.models import FindingAid

from ._parse_textract import read_textract_job


class Command(BaseCommand):
    help = "Prepare the specified finding aid for indexing."

    def add_arguments(self, parser):
        parser.add_argument("--finding-aid-id", type=int)
        parser.add_argument("--s3-key", type=str)

    def handle(self, *args, **kwargs):
        finding_aid_id = kwargs["finding-aid-id"]
        s3_key = kwargs["s3-key"]
        try:
            finding_aid = FindingAid.objects.get(pk=finding_aid_id)
        except FindingAid.DoesNotExist:
            error_msg = f"Finding aid {finding_aid_id} does not exist."
            raise CommandError(error_msg) from FindingAid.DoesNotExist

        self.stdout.write(f"Preparing finding aid {finding_aid.id} for indexing.")
        prepared_finding_aid = prepare_finding_aid(finding_aid, s3_key)
        self.stdout.write(
            f"Successfully prepared finding aid {finding_aid.id} for "
            f"indexing at {prepared_finding_aid}.",
        )


def prepare_finding_aid(finding_aid, s3_key):
    """
    Prepare the finding aid for indexing by
        1. copying the ead to an indexing directory in s3 or
        2. rendering an attached express record and saving to s3
        3. creating an indexing_env.sh file with the finding aid id, repository id,
           finding aid ark, and action (publish or preview)
        4. combining the textract output from all supplementary files as available
        5. saving the extracted supplementary files text to S3
    """

    if finding_aid.record_type == "ead":
        ead_file = finding_aid.ead_file.file
    else:
        record = render_to_string(
            "findingaids/express_record.xml",
            context={"object": finding_aid.expressrecord},
        ).encode("utf-8")
        ead_file = ContentFile(record)

    storages["default"].save(
        f"{s3_key}/finding-aid.xml",
        ead_file,
    )

    preview = finding_aid.status == "queued_preview"
    indexing_env = (
        f"export FINDING_AID_ID={finding_aid.id}\n"
        f"export REPOSITORY_ID={finding_aid.repository.code}\n"
        f"export FINDING_AID_ARK={finding_aid.ark}\n"
        f"export PREVIEW={preview}\n"
    )

    storages["default"].save(
        f"{s3_key}/indexing_env.sh",
        ContentFile(indexing_env.encode("utf-8")),
    )

    if finding_aid.supplementaryfile_set.count() >= 1:
        supplementary_files = finding_aid.supplementaryfile_set.all()
        extracted_text = get_textract_output(supplementary_files)
        with TemporaryFile() as full_text_file:
            full_text_file.write(extracted_text.encode("utf-8"))
            storages["default"].save(
                f"{s3_key}/extracted-supplementary-files-text.txt",
                full_text_file,
            )

    return s3_key


def get_textract_output(supplementary_files):
    all_extracted_text = []

    for supplementary_file in supplementary_files:
        # assumes that on supplementary file update, we clear
        # textract_output field and delete textract output from s3
        textract_output = supplementary_file.textract_output
        if not textract_output:
            continue

        textract_job = textract_output.split("/")
        bucket = textract_job[2]
        prefix = "/".join(textract_job[3:])
        textract_document = read_textract_job(bucket, prefix)
        all_extracted_text.append(textract_document["full_text"])

    return " ".join(all_extracted_text)
