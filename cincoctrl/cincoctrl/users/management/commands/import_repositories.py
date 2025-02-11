import json
import re
from pathlib import Path

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

    # oclc_share = archivegrid_harvest or worldcat_harvest?
    # date_created = "created_at"
    # date_updated = "updated_at
    # RepositoryLink  = "url" default text?

    def handle(self, *args, **options):
        filepath = options.get("filepath")
        p = re.compile(r"^\d{5}(?:[-\s]\d{4})?$")

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
                if f["parent_institution"]:
                    parent = institutions[f["parent_institution"]]
                    name = f"{parent['fields']['name']}, {f['name']}"
                else:
                    name = f["name"]
                defaults = {
                    "state": "CA",
                    "country": "US",
                    "code": code,
                    "name": name,
                    "address1": f["address1"] if f["address1"] else "",
                    "address2": f["address2"] if f["address2"] else "",
                    "city": cities[f["city"]]["fields"]["name"],
                    "description": f["description"] if f["description"] else "",
                    "zipcode": zipcode,
                    "phone": f["phone"] if f["phone"] else "",
                    "contact_email": f["email"] if f["email"] else "",
                    "aeon_url": f["aeon_URL"] if f["aeon_URL"] else "",
                }

                r, _ = Repository.objects.get_or_create(ark=f["ark"], defaults=defaults)
                link, _ = RepositoryLink.objects.get_or_create(
                    repository=r,
                    url=f["url"],
                )
                link.save()
