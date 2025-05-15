from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from cincoctrl.findingaids.management.commands.prepare_finding_aid import (
    prepare_finding_aid,
)
from cincoctrl.findingaids.models import FindingAid


class Command(BaseCommand):
    help = (
        "Prepare the specified finding aids for indexing - specify finding "
        "aids by list of ids or a single repository id."
    )

    def add_arguments(self, parser):
        # Must provide either --repository or --finding-aid-ids, but not both
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--repository",
            nargs="?",
            default=None,
            type=int,
            metavar="REPOSITORY ID",
            help="Specify Finding Aids to prepare for indexing by repository id",
        )
        group.add_argument(
            "--finding-aid-ids",
            nargs="*",
            default=None,
            type=int,
            metavar="finding-aid-id",
            help="List of Finding Aid IDs to prepare for indexing",
        )
        # Add s3_key as a named, required argument of type str
        parser.add_argument(
            "-s3",
            "--s3-key",
            nargs=1,
            required=True,
            type=str,
            help="s3 key location for storing the bundle",
        )

    def handle(self, *args, **kwargs):
        s3_key = kwargs["s3_key"]
        repository_id = kwargs["repository"]
        finding_aid_ids = kwargs["finding-aid-ids"]
        if repository_id:
            finding_aid_ids = FindingAid.objects.filter(
                repository_id=repository_id,
            ).values_list("id", flat=True)
            if not finding_aid_ids:
                error_msg = f"No finding aids found for repository {repository_id}."
                raise CommandError(error_msg)

        for finding_aid_id in finding_aid_ids:
            try:
                finding_aid = FindingAid.objects.get(pk=finding_aid_id)
            except FindingAid.DoesNotExist:
                error_msg = f"Finding aid {finding_aid_id} does not exist."
                raise CommandError(error_msg) from FindingAid.DoesNotExist

            self.stdout.write(f"Preparing finding aid {finding_aid.id} for indexing.")
            prepared_finding_aid = prepare_finding_aid(
                finding_aid,
                f"{s3_key}/{finding_aid.id}",
            )
            self.stdout.write(
                f"Successfully prepared finding aid {finding_aid.id} for "
                f"indexing at {prepared_finding_aid}.",
            )
