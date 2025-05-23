import json
import re
from pathlib import Path

import boto3
from django.core.management.base import BaseCommand

from cincoctrl.users.models import Repository
from cincoctrl.users.models import RepositoryLink


class Command(BaseCommand):
    """Import repositories for an oac4 db dump"""

    help = "Import repositories for an oac4 db dump"

    def add_arguments(self, parser):
        parser.add_argument(
            "filepath",
            help="the location of the file to import",
            type=str,
        )
        parser.add_argument(
            "-b",
            "--bucket",
            help="s3 bucket to fetch from",
            type=str,
        )

    def get_aeon_url(self, aeon_url):
        url_parts = aeon_url.split("?")
        aeon_request_url = url_parts[0] if len(url_parts) > 0 else ""
        aeon_mapping = url_parts[1] if len(url_parts) > 1 else ""
        return aeon_request_url, aeon_mapping

    def get_institution_name(self, institutions, f):
        if f["parent_institution"]:
            parent = institutions[f["parent_institution"]]
            name = f"{parent['fields']['name']}, {f['name']}"
        else:
            name = f["name"]
        return name

    def handle(self, *args, **options):
        filepath = options.get("filepath")
        p = re.compile(r"^\d{5}(?:[-\s]\d{4})?$")

        bucket = options.get("bucket", False)

        if bucket:
            client = boto3.client("s3")
            obj = client.get_object(Bucket=bucket, Key=filepath)
            data = json.loads(obj["Body"].read())
        else:
            with Path(filepath).open("r") as f:
                data = json.load(f)

        cities = {}
        counties = {}
        institutions = {}

        for x in data:
            if x["model"] == "oac.county":
                counties[x["pk"]] = x
            elif x["model"] == "oac.city":
                cities[x["pk"]] = x
            elif x["model"] == "oac.institution":
                institutions[x["pk"]] = x

        for i in institutions:
            f = institutions[i]["fields"]
            code = f["cdlpath"].replace("/", "_")
            zipcode = f["zip4"].strip()
            if len(code) == 0:
                self.stdout.write(f"ERROR\tno slug provided\t{f['name']}")
            elif len(zipcode) > 0 and not re.match(p, zipcode):
                self.stdout.write(f"ERROR\tinvalid zip ({zipcode})\t{f['name']}")
            else:
                aeon_request_url, aeon_mapping = self.get_aeon_url(
                    f.get("aeon_URL", ""),
                )

                oclc_share = f.get("archivegrid_harvest", False)
                defaults = {
                    "state": "CA",
                    "country": "US",
                    "code": code,
                    "name": self.get_institution_name(institutions, f),
                    "address1": f["address1"] if f["address1"] else "",
                    "address2": f["address2"] if f["address2"] else "",
                    "city": cities[f["city"]]["fields"]["name"],
                    "description": f["description"] if f["description"] else "",
                    "zipcode": zipcode,
                    "phone": f["phone"] if f["phone"] else "",
                    "contact_email": f["email"] if f["email"] else "",
                    "aeon_request_url": aeon_request_url,
                    "aeon_request_mappings": aeon_mapping,
                    "oclc_share": oclc_share if oclc_share is not None else False,
                    "latitude": f["latitude"],
                    "longitude": f["longitude"],
                }

                r, _ = Repository.objects.get_or_create(ark=f["ark"], defaults=defaults)
                link, _ = RepositoryLink.objects.get_or_create(
                    repository=r,
                    url=f["url"],
                    text="Website",
                )
                link.save()
