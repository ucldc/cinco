import bs4
import requests
from django.core.management.base import BaseCommand

from cincoctrl.findingaids.parser import EADParser
from cincoctrl.findingaids.parser import EADParserError


class Command(BaseCommand):
    """Parse and report errors and warning in all EAD files in the directory at a URL"""

    help = "Parse and report errors and warning in all EAD files \
            in the directory at a URL"

    def add_arguments(self, parser):
        parser.add_argument(
            "url",
            help="the location to scan",
            type=str,
        )
        parser.add_argument(
            "--validate_dtd",
            action="store_true",
            help="run the dtd validation check",
        )

    def handle(self, *args, **options):
        url = options.get("url")
        validate_dtd = options.get("validate_dtd", False)
        page = requests.get(url, timeout=30)
        page_text = bs4.BeautifulSoup(page.text, "html.parser")
        parser = EADParser()
        for link in page_text.find_all("a"):
            filename = link["href"]
            if filename and filename.endswith(".xml") and not filename.startswith("._"):
                r = requests.get(
                    url + filename,
                    allow_redirects=True,
                    stream=True,
                    timeout=30,
                )
                try:
                    parser.errors.clear()
                    parser.warnings.clear()
                    parser.parse_string(r.content)
                    if parser.is_record_express():
                        continue
                    if validate_dtd:
                        parser.validate_dtd()
                    parser.validate_required_fields()
                    parser.validate_component_titles()
                    parser.validate_dates()
                    for e in parser.errors:
                        self.stdout.write(f"{filename}\t{e}\tERROR")
                    for w in parser.warnings:
                        self.stdout.write(f"{filename}\t{w}\tWARNING")
                except EADParserError as e:
                    self.stdout.write(f"{filename}\t{e}\tERROR")
