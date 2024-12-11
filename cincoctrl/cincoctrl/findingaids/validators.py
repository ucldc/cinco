import xml.etree.ElementTree as ET

from django.core.exceptions import ValidationError


def validate_ead(file):
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        if root.find("./eadheader/eadid") is None:
            raise ValidationError("Invalid EADID")
        if root.find("./archdesc/did/unittitle") is None:
            raise ValidationError("Title not found")
        if root.find("./archdesc/did/unitid") is None:
            raise ValidationError("Collection number not found")
    except ET.ParseError:
        raise ValidationError("Invalid XML file.") from None
