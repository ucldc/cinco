from django.core.management.base import BaseCommand

from cincoctrl.findingaids.models import FindingAid


class Command(BaseCommand):
    """Mark a finding aid as unpublished"""

    help = "Mark a finding aid as unpublished"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ark",
            help="the ark of the finding aid to mark as unpublished",
            type=str,
        )

    def handle(self, *args, **options):
        ark = options.get("ark")
        f = FindingAid.objects.get(ark=ark)
        f.status = "unpublished"
        f.save()
        self.stdout.write(f"Marked finding aid {ark} as unpublished")
