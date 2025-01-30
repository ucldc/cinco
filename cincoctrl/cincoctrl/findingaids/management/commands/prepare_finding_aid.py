import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from cincoctrl.findingaids.models import FindingAid

from ._parse_textract import read_textract_job


class Command(BaseCommand):
    help = "Prepare the specified finding aid for indexing."

    def add_arguments(self, parser):
        parser.add_argument("finding_aid_id", type=int)
        parser.add_argument("s3_key", type=str)

    def handle(self, *args, **kwargs):
        finding_aid_id = kwargs["finding_aid_id"]
        s3_key = kwargs["s3_key"]
        try:
            finding_aid = FindingAid.objects.get(pk=finding_aid_id)
        except FindingAid.DoesNotExist:
            error_msg = f"Finding aid {finding_aid_id} does not exist."
            raise CommandError(error_msg) from FindingAid.DoesNotExist

        self.stdout.write(f"Preparing finding aid {finding_aid.id} for indexing.")
        prepared_finding_aid = self.prepare_finding_aid(finding_aid, s3_key)
        self.stdout.write(
            f"Successfully prepared finding aid {finding_aid.id} for "
            f"indexing at {prepared_finding_aid}.",
        )

    def prepare_finding_aid(self, finding_aid, s3_key):
        """
        Prepare the finding aid for indexing by
            1. copying the ead to an indexing directory in s3 or
            2. rendering an attached express record and saving to s3
            3. combining the textract output from all supplementary files as available
            4. saving the extracted supplementary files text to S3
        """
        s3_client = boto3.client("s3")
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        # if finding_aid.expressrecord:
        # else:
        s3_client.copy_object(
            Bucket=bucket,
            CopySource=f"{bucket}/{finding_aid.ead_file.name}",
            Key=f"{s3_key}/finding-aid.xml",
        )

        if finding_aid.supplementary_files.count() >= 1:
            supplementary_files = finding_aid.supplementary_files.all()
            extracted_text = self.get_textract_output(supplementary_files)
            s3_client.put_object(
                Bucket=bucket,
                Key=f"{s3_key}/extracted-supplementary-files-text.txt",
                Body=extracted_text.encode("utf-8"),
            )

        return s3_key

    def get_textract_output(self, supplementary_files):
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
