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

    def strip_namespace(self, node):
        for element in node.iter():
            if hasattr(element.tag, "find"):
                i = element.tag.find("}")
                if i >= 0:
                    element.tag = element.tag[i + 1 :]
        etree.cleanup_namespaces(node)
        return node

    def parse_file(self, xml_file):
        try:
            self.filename = xml_file.name
            self.xml_tree = etree.parse(xml_file)
            self.root = self.strip_namespace(self.xml_tree.getroot())
        except etree.XMLSyntaxError as e:
            msg = f"Could not parse XML file: {e}"
            raise EADParserError(msg) from None

    def parse_string(self, xml_str, filename):
        try:
            self.filename = filename
            self.xml_tree = None
            self.root = self.strip_namespace(etree.fromstring(xml_str))
        except etree.XMLSyntaxError as e:
            msg = f"Could not parse XML file: {e}"
            raise EADParserError(msg) from None

    def parse_parent_ark(self):
        eadid = self.root.find("./eadheader/eadid")
        return eadid.attrib.get(
            "{http://www.cdlib.org/path/}parent",
            None,
        )

    def parse_ark(self):
        eadid = self.root.find("./eadheader/eadid")
        ark = None
        if eadid is not None:
            if "identifier" in eadid.attrib:
                ark = eadid.attrib["identifier"]
            elif eadid.attrib.get("url"):
                ark = eadid.attrib.get("url")
            elif eadid.text:
                ark = eadid.text

        if ark:
            m = re.search(r"(ark:/\d{5}/[a-zA-z0-9]+)", ark)
            ark = m.group(0) if m else None

        return ark

    def get_href(self, attribs):
        if "href" in attribs:
            href = attribs["href"]
        else:
            href = attribs.get("{http://www.w3.org/1999/xlink}href", None)
        return href

    def parse_otherfindaids(self):
        others = []
        for other in self.root.findall(".//otherfindaid"):
            others.extend(
                [
                    {
                        "href": self.get_href(ref.attrib),
                        "text": self.node_to_string(ref),
                    }
                    for ref in other.findall(".//extref")
                ],
            )
        return others

    def remove_extrefs(self, other):
        for item in other.findall(".//item"):
            item.getparent().remove(item)
        for extref in other.findall(".//extref"):
            extref.getparent().remove(extref)

    def get_otherlist(self):
        other = self.root.find(".//otherfindaid")
        if other is None:
            archdesc = self.root.find(".//archdesc")
            other = etree.SubElement(archdesc, "otherfindaid")
            other.attrib["id"] = "otherfindaid"
            head = etree.SubElement(other, "head")
            head.text = "Additional collection guides"
        else:
            self.remove_extrefs(other)
        item_list = other.find("./list")
        if item_list is None:
            item_list = etree.SubElement(other, "list")
        return item_list

    def update_otherfindaids(self, supp_files):
        item_list = self.get_otherlist()
        for f in supp_files:
            self.add_findingaid_link(item_list, f["url"], f["text"])

    def add_findingaid_link(self, other_list, href, text):
        item = etree.SubElement(other_list, "item")
        extref = etree.SubElement(item, "extref")
        extref.attrib["href"] = href
        extref.text = text

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

    def has_dtd(self):
        return (
            self.xml_tree is not None and self.xml_tree.docinfo.internalDTD is not None
        )

    def validate_dtd(self):
        if self.has_dtd():
            with Path("cincoctrl/findingaids/files/ead2002.dtd").open("r") as f:
                dtd = etree.DTD(StringIO(f.read()))

            try:
                if not dtd.validate(self.root):
                    for e in dtd.error_log.filter_from_errors():
                        msg = self.parse_dtd_error(e)
                        self.warnings.append(msg)
            except etree.XMLSyntaxError as e:
                self.warnings.append(f"Could not validate dtd: {e}"[:255])

    def is_record_express(self):
        author = self.root.find("./eadheader/filedesc/titlestmt/author")
        return author is not None and author.text and "RecordEXPRESS" in author.text

    def node_to_string(self, node):
        return (
            etree.tostring(node, encoding="utf-8", method="text", with_tail=False)
            .decode()
            .strip()
        )

    def update_eadid(self, filename):
        node = self.root.find("./eadheader/eadid")
        node.text = filename

    def get_title_node(self):
        node = self.root.find("./archdesc/did/unittitle")
        if node is None:
            node = self.root.find("./eadheader/filedesc/titlestmt/titleproper")
        return node

    def get_collection_number(self):
        number_node = self.root.find("./archdesc/did/unitid")
        if number_node is None:
            return self.filename
        number = self.node_to_string(number_node)
        if len(number) == 0:
            return self.filename
        return number

    def validate_required_fields(self):
        node = self.get_title_node()
        if node is None:
            self.errors.append("Failed to parse Title")
        elif len(self.node_to_string(node)) == 0:
            self.errors.append("No value in Title")

    def extract_ead_fields(self):
        title_node = self.get_title_node()
        title = self.node_to_string(title_node)
        number = self.get_collection_number()
        ark = self.parse_ark()
        return title, number, ark

    def validate_component_titles(self):
        comps = self.root.findall(".//c01")
        for c in comps:
            self.get_component_title(c)

    def validate_component_level(self, c, cid):
        if c.attrib.get("level", "") == "collection":
            self.warnings.append(
                f"Components cannot have level=collection: {cid}",
            )

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
                        self.warnings.append(f"No title for non-empty component: {cid}")

        self.validate_component_level(c, cid)

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
