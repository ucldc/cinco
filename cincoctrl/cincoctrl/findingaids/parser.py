import re
from io import StringIO
from pathlib import Path

from lxml import etree


class EADParserError(Exception):
    pass


class EADParser:
    def __init__(self):
        self.warnings = []
        self.errors = []
        self.ark_dir = None
        with Path("cincoctrl/findingaids/files/ead2002.dtd").open("r") as f:
            self.dtd = etree.DTD(StringIO(f.read()))

    def parse_file(self, xml_file):
        try:
            self.root = etree.parse(xml_file).getroot()
        except etree.XMLSyntaxError as e:
            msg = f"Could not parse XML file: {e}"
            raise EADParserError(msg) from None

    def parse_string(self, xml_str):
        try:
            self.root = etree.fromstring(xml_str)
        except etree.XMLSyntaxError as e:
            msg = f"Could not parse XML file: {e}"
            raise EADParserError(msg) from None

    def parse_arks(self):
        eadid = self.root.find("./eadheader/eadid")
        return eadid.attrib.get("identifier", None), eadid.attrib.get(
            "{http://www.cdlib.org/path/}parent",
            None,
        )

    def set_ark_dir(self, ark):
        a = ark.split("/")
        self.ark_dir = f"/data/{a[1]}/{a[2][-2:]}/{a[2]}/files/"

    def get_href(self, attribs):
        if "href" in attribs:
            href = attribs["href"]
        else:
            href = attribs.get("{http://www.w3.org/1999/xlink}href", None)
        if self.ark_dir and not self.ark_dir in href and not href.startswith("http"):
            href = self.ark_dir + href
        return href

    def parse_otherfindaids(self):
        others = []
        for other in self.root.findall(".//otherfindaid"):
            others.extend(
                [
                    {"href": self.get_href(ref.attrib), "text": ref.text.strip()}
                    for ref in other.findall(".//extref")
                ],
            )
        return others

    def update_otherfindaids(self, urls):
        for other in self.root.findall(".//otherfindaid"):
            for ref in other.findall(".//extref"):
                href = self.get_href(ref.attrib)
                # remove any of the old junk if present
                ref.attrib.pop("{http://www.w3.org/1999/xlink}href", None)
                ref.attrib.pop("{http://www.w3.org/1999/xlink}role", None)
                ref.attrib.pop("role", None)

                # set the new url
                ref.attrib["href"] = urls[href]

    def to_string(self):
        return etree.tostring(
            self.root,
            encoding="utf-8",
            pretty_print=True,
            xml_declaration=True,
        )

    def parse_dtd_error(self, e):
        pattern = re.compile(r"(.*), expecting \((.*)\), got \((.*)\)")
        match = pattern.search(e.message)
        if match:
            allowed = []
            required = []
            for x in match.group(2).split(" , "):
                if x.startswith("("):
                    inner_text = re.findall(r"\((.*?)\)", x)
                    if len(inner_text) > 0:
                        innards = inner_text[0].split(" | ")
                        allowed.extend(innards)
                        if x.endswith("+"):
                            required.extend(innards)
                elif x.endswith(("*", "?")):
                    allowed.append(x.strip("*").strip("?"))
                else:
                    allowed.append(x.strip("+"))
                    required.append(x.strip("+"))
            found = match.group(3).strip().split(" ")
            unexpected = list(set(found) - set(allowed))
            missing = list(set(required) - set(found))
            msg = f"{match.group(1)}"
            if len(unexpected) > 0:
                msg += f" - unexpected element {','.join(unexpected)}"
            if len(missing) > 0:
                msg += f" - missing required elements {','.join(missing)}"
        else:
            msg = f"Could not validate dtd: {e.message}"[:255]
        return msg

    def validate_dtd(self):
        try:
            if not self.dtd.validate(self.root):
                for e in self.dtd.error_log.filter_from_errors():
                    msg = self.parse_dtd_error(e)
                    self.warnings.append(msg)
        except etree.XMLSyntaxError as e:
            self.warnings.append(f"Could not validate dtd: {e}"[:255])

    required_fields = [
        ("./eadheader/eadid", "EADID"),
        ("./archdesc/did/unittitle", "Title"),
        ("./archdesc/did/unitid", "Collection number"),
    ]

    def validate_required_fields(self):
        for field, label in self.required_fields:
            if self.root.find(field) is None:
                self.errors.append(f"Failed to parse {label}")

    def extract_ead_fields(self):
        title_node = self.root.find("./archdesc/did/unittitle")
        number_node = self.root.find("./archdesc/did/unitid")
        return title_node.text, number_node.text

    def validate_component_titles(self):
        comps = self.root.findall(".//c01")
        for c in comps:
            self.get_component_title(c)

    def get_component_title(self, c):
        cid = c.attrib.get("id", c.tag)
        # if we have a unittitle or unitdate in this component we're good
        t = self.get_element_value(c, "./did/unittitle")
        d = self.get_element_value(c, "./did/unitdate")
        if t is None and d is None:
            # fall back to container data
            containers = c.findall("./did/container")
            if len(containers) == 0:
                # last chance, use unitid
                uid = self.get_element_value(c, "./did/unitid")
                if uid is None:
                    # if comp is empty it will be ignore, it's ok
                    text = etree.tostring(c, encoding="utf-8", method="text").strip()
                    if len(text) > 0:
                        # not empty but no title info, indexing will fail
                        self.errors.append(f"No title for non-empty component: {cid}")

        for e in c:
            if e.tag is not etree.Comment and re.match(r"c\d\d", e.tag):
                self.get_component_title(e)

    def get_element_value(self, e, path):
        n = e.find(path)
        if n is not None:
            # get the text from all child components a remove whitespace
            # this allows us to determine if there is displayable data in this comp
            text = etree.tostring(n, encoding="utf-8", method="text").strip()
            if len(text) > 0:
                return text
        return None

    def validate_dates(self):
        date_nodes = self.root.findall(".//unitdate[@normal]")
        for node in date_nodes:
            self.validate_date(node)

    def validate_date(self, node):
        date_str = node.attrib["normal"].strip()
        if "undated" not in date_str.lower() and len(date_str) > 0:
            # valid date format: start-date/end-date,nonsequential-date
            # (ex: 2000-01-01/2001-01-01,2023-01-01)
            parts = date_str.split("/")
            max_dates = 2
            if len(parts) > max_dates:
                # / is the divider between start and end dates
                # *should* only appear once but if more just a warning
                self.warnings.append(f"Invalid date format {date_str}")
            elif len(parts) == max_dates:
                # if there is a slash try to parse start and end years
                # warn if not parseable
                start_year = self.get_year(parts[0])
                end_year = self.get_year(parts[1])
                if not start_year or not end_year:
                    if not start_year:
                        self.warnings.append(f"Could not parse start year: {date_str}")
                    if not end_year:
                        self.warnings.append(f"Could not read end year: {date_str}")
                elif end_year < start_year:
                    # warn if end year is before start year, it will be ignored
                    # in indexing but obviously incorrect
                    self.warnings.append(
                        f"End year ({end_year}) before start year ({start_year})",
                    )
            else:
                start_year = self.get_year(parts[0])
                if not start_year:
                    self.warnings.append(f"Could not parse start year: {date_str}")

    def get_year(self, date_str):
        if date_str == "null":
            return 0
        m = re.search(r"([-]?(\d)+)", date_str)
        if m:
            return int(m.group())
        return False
