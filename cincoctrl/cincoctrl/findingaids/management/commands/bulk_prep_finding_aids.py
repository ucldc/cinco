import logging
from datetime import UTC
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from cincoctrl.airflow_client.mwaa_api_client import trigger_dag
from cincoctrl.findingaids.management.commands.prepare_finding_aid import (
    prepare_finding_aid,
)
from cincoctrl.findingaids.models import FindingAid

logger = logging.getLogger(__name__)


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
        s3_key = kwargs["s3-key"]
        repository_id = kwargs.get("repository")
        finding_aid_ids = kwargs.get("finding-aid-ids")

        if repository_id:
            finding_aids = FindingAid.objects.filter(repository_id=repository_id)
        elif finding_aid_ids:
            finding_aids = FindingAid.objects.filter(id__in=finding_aid_ids)

        bulk_prep_finding_aids(finding_aids, s3_key)


def bulk_prep_finding_aids(finding_aids, s3_key):
    for finding_aid in finding_aids:
        prepare_finding_aid(
            finding_aid,
            f"{s3_key}/{finding_aid.id}",
        )


def bulk_index_finding_aids(finding_aids: QuerySet):
    now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
    s3_key = f"indexing/bulk/{now_str}"

    for finding_aid in finding_aids:
        finding_aid.queue_status()

    if settings.ENABLE_AIRFLOW:
        logger.info("bulk indexing %s finding aids", finding_aids.count())
        bulk_prep_finding_aids(finding_aids, s3_key)
        trigger_dag(
            "bulk_index_finding_aids",
            {"s3_key": s3_key},
            related_models=finding_aids,
            dag_run_prefix=f"{settings.AIRFLOW_PROJECT_NAME}__bulk_{now_str}",
        )
