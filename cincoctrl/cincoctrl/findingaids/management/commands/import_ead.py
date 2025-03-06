import bs4
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
        parser.add_argument(
            "--directory",
            action="store_true",
            help="if the url points to an entire directory rather than a single EAD",
        )

    def validate_ead(self, filename, text):
        parser = EADParser()
        parser.parse_string(text)
        parser.validate_dtd()
        parser.validate_required_fields()
        parser.validate_component_titles()
        parser.validate_dates()
        return parser

    def process_supp_files(self, parser, doc_url, finding_aid):
        # get and upload any supp files
        urls = {}
        for order, a in enumerate(parser.parse_otherfindaids()):
            r = requests.get(
                (doc_url + a["href"]),
                allow_redirects=True,
                timeout=30,
            )
            r.raise_for_status()
            sfilename = a["href"].split("/")[-1]
            pdf_file = SimpleUploadedFile(sfilename, r.content)
            s = SupplementaryFile.objects.create(
                finding_aid=finding_aid,
                title=a["text"],
                pdf_file=pdf_file,
                order=order,
            )
            urls[a["href"]] = s.pdf_file.url
        # update links in original EAD
        if len(urls) > 0:
            parser.update_otherfindaids(urls)

    def import_ead(self, url, filename, doc_url):
        r = requests.get(url, allow_redirects=True, timeout=30)
        r.raise_for_status()

        try:
            parser = self.validate_ead(filename, r.content)
            if len(parser.errors) > 0:
                self.stdout.write(f"Failed to import {filename}")
                for e in parser.errors:
                    self.stdout.write(f"\t{filename}\t{e}\tERROR")
                return

            ark, parent_ark = parser.parse_arks()
            repo = Repository.objects.get(ark=parent_ark)
            parser.set_ark_dir(ark)

            if FindingAid.objects.filter(ark=ark).exists():
                self.stdout.write(f"Abort: {ark} already exists")
                return

            # create the finding aid without the file at first
            f, _ = FindingAid.objects.get_or_create(
                repository=repo,
                ark=ark,
                record_type="ead",
            )

            self.process_supp_files(parser, doc_url, f)

            # add the new ead file
            ead_file = SimpleUploadedFile(
                filename,
                parser.to_string().encode(encoding="utf-8"),
            )
            f.ead_file = ead_file
            f.save()
            self.stdout.write(f"Successfully imported {ark}")
            for s in f.supplementaryfile_set.all():
                self.stdout.write(f"\tImported: {s}")
        except EADParserError as e:
            self.stdout.write(f"{filename}\t{e}\tERROR")

    def handle(self, *args, **options):
        url = options.get("url")
        doc_url = options.get("doc_url", "https://cdn.calisphere.org")
        is_directory = options.get("directory", False)

        if is_directory:
            page = requests.get(url, timeout=30)
            page_text = bs4.BeautifulSoup(page.text, "html.parser")
            for link in page_text.find_all("a"):
                filename = link["href"]
                if (
                    filename
                    and filename.endswith(".xml")
                    and not filename.startswith("._")
                ):
                    self.import_ead(url + filename, filename, doc_url)
        else:
            filename = url.split("/")[-1]
            self.import_ead(url, filename, doc_url)
