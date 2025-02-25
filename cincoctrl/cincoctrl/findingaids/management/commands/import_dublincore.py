import json
from pathlib import Path

import boto3
from django.core.management.base import BaseCommand

from cincoctrl.findingaids.models import ExpressRecordCreator
from cincoctrl.findingaids.models import ExpressRecordSubject
from cincoctrl.findingaids.models import FindingAid

CREATOR_MAP = {
    "person": "persname",
    "family": "famname",
    "organization": "corpname",
}

SUBJECT_MAP = {
    "topic": "subject",
    "name_person": "persname",
    "name_family": "famname",
    "name_organization": "corpname",
    "title": "title",
    "geo": "geogname",
    "function": "function",
    "genre": "genreform",
    "occupation": "occupation",
}


class Command(BaseCommand):
    """Import dublincore fields to record express"""

    help = "Import dublincore fields to record express"

    def add_arguments(self, parser):
        parser.add_argument(
            "filepath",
            help="path to the export file",
            type=str,
        )
        parser.add_argument(
            "-b",
            "--bucket",
            help="s3 bucket to fetch from",
            type=str,
        )

    def handle(self, *args, **options):
        filepath = options.get("filepath")
        bucket = options.get("bucket", False)

        if bucket:
            client = boto3.client("s3")
            obj = client.get_object(Bucket=bucket, Key=filepath)
            data = json.loads(obj["Body"].read())
        else:
            with Path(filepath).open("r") as f:
                data = json.load(f)

        for d in data:
            ark = d["fields"]["object_id"]
            if FindingAid.objects.filter(ark=ark).exists():
                term = d["fields"]["term"]
                qualifier = d["fields"]["qualifier"]
                value = d["fields"]["content"]
                if term == "CR":
                    f = FindingAid.objects.get(ark=ark)
                    if qualifier in CREATOR_MAP:
                        creator_type = CREATOR_MAP[qualifier]
                        ExpressRecordCreator.objects.get_or_create(
                            record=f.expressrecord,
                            creator_type=creator_type,
                            value=value,
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"unknown qualifier ({term}, {qualifier}): {value}",
                            ),
                        )
                elif term in ("SUB", "CVR", "TYP"):
                    if qualifier in SUBJECT_MAP:
                        subject_type = SUBJECT_MAP[qualifier]
                        ExpressRecordSubject.objects.get_or_create(
                            record=f.expressrecord,
                            subject_type=subject_type,
                            value=value,
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"unknown qualifier ({term}, {qualifier}): {value}",
                            ),
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"unknown term: {term}, {qualifier}"),
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f"no finding aid with ark {ark}"),
                )
