import json
import re
from pathlib import Path

import boto3
import requests
from django.core.management.base import BaseCommand

from cincoctrl.findingaids.models import ExpressRecord
from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import Language
from cincoctrl.findingaids.models import SupplementaryFile
from cincoctrl.findingaids.utils import download_pdf
from cincoctrl.users.models import Repository


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

    def import_finding_aid(self, repo_ark, ark, fields):
        repo = Repository.objects.get(ark=repo_ark)
        start_year, end_year = self.get_start_end_years(fields["date_iso"])
        if FindingAid.objects.filter(ark=ark).exists():
            return
        f = FindingAid.objects.create(
            ark=ark,
            repository=repo,
            collection_title=fields["title"],
            collection_number=fields["local_identifier"],
            record_type="express",
        )
        kwargs = {
            "title_filing": fields["title_filing"],
            "date": fields["date_dacs"],
            "extent": fields["extent"],
            "accessrestrict": fields["accessrestrict"],
            "userestrict": fields["userestrict"],
            "acqinfo": fields["acqinfo"],
            "scopecontent": fields["scopecontent"],
            "bioghist": fields["bioghist"],
            "online_items_url": fields["online_items_url"],
            "date_created": fields["created_at"],
            "date_updated": fields["updated_at"],
        }
        if start_year:
            kwargs["start_year"] = int(start_year)
        if end_year:
            kwargs["end_year"] = int(end_year)
        e = ExpressRecord.objects.create(finding_aid=f, **kwargs)
        if Language.objects.filter(code=fields["language"]).exists():
            lang = Language.objects.get(code=fields["language"])
            e.language.add(lang)

    def import_supp_file(self, fields):
        ark = fields["collection_record"]
        filename = fields["filename"]
        if not FindingAid.objects.filter(ark=ark).exists():
            self.stdout.write(
                self.style.ERROR(
                    f"ERROR\t{ark}\t\trecord not found\t{filename}",
                ),
            )
        else:
            ark_tail = ark.split("/")[-1]
            f = FindingAid.objects.get(ark=ark)
            doc_url = f"https://cdn.calisphere.org/data/13030/{ark[-2:]}/{ark_tail}/files/{filename}"
            cleaned_name = filename[:-4].replace(" ", "_")
            ch = ["(", ")", "'", ","]
            for c in ch:
                cleaned_name = cleaned_name.replace(c, "")

            if f.supplementaryfile_set.filter(
                title=fields["label"],
                pdf_file__contains=cleaned_name,
            ).exists():
                # file has already been imported: Abort
                return
            try:
                pdf_file = download_pdf(doc_url, filename)
                order = f.supplementaryfile_set.count()
                SupplementaryFile.objects.create(
                    finding_aid=f,
                    title=fields["label"],
                    pdf_file=pdf_file,
                    order=order,
                )
            except requests.exceptions.HTTPError:
                self.stdout.write(
                    self.style.ERROR(
                        f"ERROR\t{ark}\t\tsupp file {doc_url} not found",
                    ),
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

        repos = {}
        for d in data:
            if d["model"] == "oac.institution":
                repos[d["pk"]] = d["fields"]["ark"]

        for d in data:
            fields = d["fields"]
            if d["model"] == "collection_record.collectionrecord":
                repo_ark = repos[fields["publisher"]]
                if Repository.objects.filter(ark=repo_ark).exists():
                    self.import_finding_aid(repo_ark, d["pk"], fields)
                else:
                    self.stdout.write(
                        self.style.ERROR(f"ERROR\t{d["pk"]}\t{repo_ark}\tmissing repo"),
                    )
            elif d["model"] == "collection_record.supplementalfile":
                self.import_supp_file(fields)
