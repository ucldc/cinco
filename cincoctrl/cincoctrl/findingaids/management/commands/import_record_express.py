import json
import re
from pathlib import Path

import boto3
import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand

from cincoctrl.findingaids.models import ExpressRecord
from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import SupplementaryFile
from cincoctrl.users.models import Repository

# author_statement = TextField(blank=True)
# preferred_citation = TextField(blank=True)
# processing_information = TextField(blank=True)

# date_created = DateTimeField(auto_now_add=True)
# date_updated = DateTimeField(auto_now=True)
# "created_at": "2012-05-14T15:18:11",
# "updated_at": "2022-10-06T13:42:18",


class Command(BaseCommand):
    """Import records express collections from export"""

    help = "Import records express collections from export"

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

    def get_year(self, s):
        p = r"\d{4}"
        m = re.match(p, s)
        if m:
            return int(m.group(0))
        return None

    def get_start_end_years(self, date):
        x = date.split("/")
        start_year = self.get_year(x[0]) if len(x) > 0 else None
        end_year = self.get_year(x[1]) if len(x) > 1 else None
        return start_year, end_year

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

        repos = {}
        for d in data:
            if d["model"] == "oac.institution":
                repos[d["pk"]] = d["fields"]["ark"]

        for d in data:
            fields = d["fields"]
            if d["model"] == "collection_record.collectionrecord":
                repo_ark = repos[fields["publisher"]]
                if Repository.objects.filter(ark=repo_ark).exists():
                    repo = Repository.objects.get(ark=repo_ark)
                    start_year, end_year = self.get_start_end_years(fields["date_iso"])
                    f = FindingAid.objects.create(
                        ark=d["pk"],
                        repository=repo,
                        collection_title=fields["title"],
                        collection_number=fields["local_identifier"],
                        record_type="express",
                    )
                    kwargs = {
                        "title_filing": fields["title_filing"],
                        "date": fields["date_dacs"],
                        "extent": fields["extent"],
                        "language": fields["language"],
                        "accessrestrict": fields["accessrestrict"],
                        "userestrict": fields["userestrict"],
                        "acqinfo": fields["acqinfo"],
                        "scopecontent": fields["scopecontent"],
                        "bioghist": fields["bioghist"],
                        "online_items_url": fields["online_items_url"],
                    }
                    if start_year:
                        kwargs["start_year"] = int(start_year)
                    if end_year:
                        kwargs["end_year"] = int(end_year)
                    ExpressRecord.objects.create(finding_aid=f, **kwargs)
                else:
                    self.stdout.write(
                        self.style.ERROR(f"ERROR: no repository with ark {repo_ark}"),
                    )
            elif d["model"] == "collection_record.supplementalfile":
                ark = fields["collection_record"]
                filename = fields["filename"]
                f = FindingAid.objects.get(ark=ark)
                doc_url = f"https://cdn.calisphere.org/data/13030/{ark[-2]}/{ark}/files/{filename}"
                r = requests.get(doc_url, allow_redirects=True, timeout=30)
                pdf_file = SimpleUploadedFile(filename, r.content)
                SupplementaryFile.objects.create(
                    finding_aid=f,
                    title=fields["label"],
                    pdf_file=pdf_file,
                )
