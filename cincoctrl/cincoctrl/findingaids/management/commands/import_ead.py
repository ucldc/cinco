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

    def validate_ead(self, filename, text):
        parser = EADParser()
        parser.parse_string(text)
        parser.validate_dtd()
        parser.validate_required_fields()
        parser.validate_component_titles()
        parser.validate_dates()
        for e in parser.errors:
            self.stdout.write(f"{filename}\t{e}\tERROR")
        for w in parser.warnings:
            self.stdout.write(f"{filename}\t{w}\tWARNING")
        return parser

    def process_supp_files(self, parser, doc_url, finding_aid):
        # get and upload any supp files
        urls = {}
        order = 0
        for a in parser.parse_otherfindaids():
            r = requests.get(
                (doc_url + a["href"]),
                allow_redirects=True,
                timeout=30,
            )
            sfilename = a["href"].split("/")[-1]
            pdf_file = SimpleUploadedFile(sfilename, r.content)
            s = SupplementaryFile.objects.create(
                finding_aid=finding_aid,
                title=a["text"],
                pdf_file=pdf_file,
                order=order
            )
            urls[a["href"]] = s.pdf_file.url
            order += 1
        # update links in original EAD
        if len(urls) > 0:
            parser.update_otherfindaids(urls)

    def handle(self, *args, **options):
        url = options.get("url")
        filename = url.split("/")[-1]
        doc_url = options.get("doc_url", "https://cdn.calisphere.org")

        r = requests.get(url, allow_redirects=True, timeout=30)
        r.raise_for_status()

        try:
            parser = self.validate_ead(filename, r.content)
            if len(parser.errors) == 0:
                ark, parent_ark = parser.parse_arks()
                repo = Repository.objects.get(ark=parent_ark)
                parser.set_ark_dir(ark)

                # create the finding aid without the file at first
                f, _ = FindingAid.objects.get_or_create(
                    repository=repo,
                    ark=ark,
                    record_type="ead"
                )

                self.process_supp_files(parser, doc_url, f)

                # add the new ead file
                ead_file = SimpleUploadedFile(filename, parser.to_string().encode(encoding="utf-8"))
                f.ead_file = ead_file
                f.save()
        except EADParserError as e:
            self.stdout.write(f"{filename}\t{e}\tERROR")
