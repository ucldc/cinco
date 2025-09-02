from django.core.management.base import BaseCommand

from cincoctrl.findingaids.models import FindingAid


class Command(BaseCommand):
    """Remove a finding aid"""

    help = "Remove a finding aid"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ark",
            help="the ark of the finding aid to delete",
            type=str,
        )

    def handle(self, *args, **options):
        ark = options.get("ark")
        f = FindingAid.objects.get(ark=ark)
        f.delete()
        self.stdout.write(f"Deleted finding aid {ark}")
