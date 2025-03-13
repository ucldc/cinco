import bs4
import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand

from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import SupplementaryFile
from cincoctrl.findingaids.parser import EADParser
from cincoctrl.findingaids.parser import EADParserError
from cincoctrl.users.models import Repository


class URLError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


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

    def get_ark_dir(self, ark):
        a = ark.split("/")
        return f"/data/{a[1]}/{a[2][-2:]}/{a[2]}/files/"

    def normalize_pdf_href(self, href, doc_url, ark_dir):
        if href.startswith(doc_url):
            return href
        if href.startswith("https://oac.cdlib.org/"):
            return href.replace("https://oac.cdlib.org/", doc_url)
        if href.startswith("http"):
            msg = f"Can't download external document {href}"
            raise URLError(msg)
        if ark_dir and not ark_dir in href:
            href = ark_dir + href
        return doc_url + href

    def process_supp_files(self, parser, doc_url, ark_dir, finding_aid):
        # get and upload any supp files
        for order, a in enumerate(parser.parse_otherfindaids()):
            try:
                url = self.normalize_pdf_href(a["href"], doc_url, ark_dir)
                r = requests.get(
                    url,
                    allow_redirects=True,
                    timeout=30,
                    stream=True,
                )
                r.raise_for_status()
                sfilename = a["href"].split("/")[-1]
                pdf_file = SimpleUploadedFile(sfilename, r.content)
                SupplementaryFile.objects.create(
                    finding_aid=finding_aid,
                    title=a["text"],
                    pdf_file=pdf_file,
                    order=order,
                )
            except requests.exceptions.HTTPError:
                self.stdout.write(f"Supp file {a['href']} not found")
            except URLError as e:
                self.stdout.write(e.message)

        # update links in original EAD
        if finding_aid.supplementaryfile_set.exists():
            parser.update_otherfindaids(
                [
                    {"url": f.pdf_file.url, "text": f.title}
                    for f in finding_aid.supplementaryfile_set.all()
                ],
            )

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
            ark_dir = self.get_ark_dir(ark)

            if FindingAid.objects.filter(ark=ark).exists():
                self.stdout.write(f"Abort: {ark} already exists")
                return

            # create the finding aid without the file at first
            f, _ = FindingAid.objects.get_or_create(
                repository=repo,
                ark=ark,
                record_type="ead",
            )

            self.process_supp_files(parser, doc_url, ark_dir, f)

            # add the new ead file
            ead_file = SimpleUploadedFile(
                filename,
                parser.to_string(),
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
