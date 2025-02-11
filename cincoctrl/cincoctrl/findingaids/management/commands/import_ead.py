import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand

from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import SupplementaryFile
from cincoctrl.findingaids.parser import EADParser
from cincoctrl.findingaids.parser import EADParserError
from cincoctrl.users.models import Repository


class Command(BaseCommand):
    """Import a single EAD file and any supplemental files"""

    help = "Import a single EAD file and any supplemental files"

    def add_arguments(self, parser):
        parser.add_argument(
            "url",
            help="URL of the finding aid",
            type=str,
        )
        parser.add_argument(
            "-d",
            "--docurl",
            type=str,
        )

    def handle(self, *args, **options):
        url = options.get("url")
        filename = url.split("/")[-1]
        doc_url = options.get("doc_url", "https://cdn.calisphere.org")

        r = requests.get(url, allow_redirects=True, timeout=30)
        r.raise_for_status()

        try:
            parser = EADParser()
            parser.parse_string(r.content)
            parser.validate_dtd()
            parser.validate_required_fields()
            parser.validate_component_titles()
            parser.validate_dates()
            for e in parser.errors:
                self.stdout.write(f"{filename}\t{e}\tERROR")
            for w in parser.warnings:
                self.stdout.write(f"{filename}\t{w}\tWARNING")
            if len(parser.errors) == 0:
                ead_file = SimpleUploadedFile(filename, r.content)
                ark, parent_ark = parser.parse_arks()
                repo = Repository.objects.get(ark=parent_ark)
                if not ark or not FindingAid.objects.filter(ark=ark).exists():
                    f = FindingAid.objects.create(
                        repository=repo,
                        ark=ark,
                        ead_file=ead_file,
                        record_type="ead",
                    )
                    f.save()
                else:
                    f = FindingAid.objects.get(ark=ark)
                for a in parser.parse_otherfindaids():
                    r = requests.get(
                        (doc_url + a["href"]),
                        allow_redirects=True,
                        timeout=30,
                    )
                    sfilename = a["href"].split("/")[-1]
                    pdf_file = SimpleUploadedFile(sfilename, r.content)
                    SupplementaryFile.objects.create(
                        finding_aid=f,
                        title=a["text"],
                        pdf_file=pdf_file,
                    )
        except EADParserError as e:
            self.stdout.write(f"{filename}\t{e}\tERROR")
