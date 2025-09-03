import boto3
from django.core import settings
from django.core.management.base import BaseCommand

from cincoctrl.findingaids.models import FindingAid


class Command(BaseCommand):
    """Bulk remove finding aids"""

    help = "Bulk remove finding aids"

    def add_arguments(self, parser):
        parser.add_argument(
            "--s3_key",
            help="""The s3_key where a csv of 'finding aid ark, repository code' pairs
                    to be deleted are stored (relative to removals/)""",
            type=str,
        )

    def handle(self, *args, **options):
        s3_key = options.get("s3_key")
        s3_client = boto3.client("s3")
        obj = s3_client.get_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=f"removals/{s3_key}",
        )
        body = obj["Body"].read().decode("utf-8")
        for line in body.splitlines():
            ark, repo_code = line.split(",")
            ark = ark.strip()
            f = FindingAid.objects.get(ark=ark)
            f.delete()
            self.stdout.write(f"Deleted finding aid {ark}")
