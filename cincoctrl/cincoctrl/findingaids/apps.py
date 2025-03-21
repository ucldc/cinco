from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FindingaidsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cincoctrl.findingaids"
    verbose_name = _("Finding Aids")

    def ready(self):
        pass
