from django.core.exceptions import ValidationError

from cincoctrl.findingaids.parser import EADParser
from cincoctrl.findingaids.parser import EADParserError


def validate_ead(file):
    try:
        parser = EADParser()
        parser.parse_file(file)
        parser.validate_required_fields()
        parser.validate_component_titles()
        if len(parser.errors) > 0:
            # TODO: can we include all the error messages?
            raise ValidationError(parser.errors[0]) from None
    except EADParserError as e:
        raise ValidationError(str(e)) from None
