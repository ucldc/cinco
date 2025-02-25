from django import template

# from cincoctrl.findingaids.models import get_record_type_label

register = template.Library()


@register.simple_tag
def record_type_label(record_type, *args, **kwargs):
    return ""
