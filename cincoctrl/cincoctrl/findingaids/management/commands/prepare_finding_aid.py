from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from cincoctrl.findingaids.management.commands._prepare_for_indexing import (
    prepare_finding_aid,
)
from cincoctrl.findingaids.models import FindingAid


class Command(BaseCommand):
    help = "Prepare the specified finding aid for indexing."

    def add_arguments(self, parser):
        parser.add_argument("--finding-aid-id", type=int)
        parser.add_argument("--s3-key", type=str)

    def handle(self, *args, **kwargs):
        finding_aid_id = kwargs["finding_aid_id"]
        s3_key = kwargs["s3_key"]
        try:
            finding_aid = FindingAid.objects.get(pk=finding_aid_id)
        except FindingAid.DoesNotExist:
            error_msg = f"Finding aid {finding_aid_id} does not exist."
            raise CommandError(error_msg) from FindingAid.DoesNotExist

        self.stdout.write(f"Preparing finding aid {finding_aid.id} for indexing.")
        prepared_finding_aid = prepare_finding_aid(finding_aid, s3_key)
        self.stdout.write(
            f"Successfully prepared finding aid {finding_aid.id} for "
            f"indexing at {prepared_finding_aid}.",
        )
