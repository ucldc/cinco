"""
To kick off a bulk indexing job, run:
    python manage.py bulk_index_finding_aids

Arguments:
--finding-aid-ids: a list of finding aid ids to index. one of
    either --finding-aid-ids or --repository-id is required
--repository-id: will index all finding aids related to this
    repository, either this, or a list of finding aid ids is required
--s3-key: [optional] s3 key to customize where the job's working
    files are stored, will use {settings.AWS_STORAGE_BUCKET_NAME}/media/
    (defined in django settings), followed by {s3_key}, by default:
    {AWS_STORAGE_BUCKET_NAME}/media/indexing/bulk/{now}
--force-publish: [optional] if True, will force publish all finding aids,
    default is False.

Constructs a queryset from the list of ids or the repository id, sets
the status field on each finding aid, creates the
finding-aid-supplemental-file-indexing-env-bundle for each finding aid,
and triggers the bulk_index_finding_aids dag with the s3 prefix of the
job's working files as the argument.
"""

import logging
from datetime import UTC
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from cincoctrl.airflow_client.mwaa_api_client import trigger_dag
from cincoctrl.findingaids.management.commands._prepare_for_indexing import (
    bulk_prep_finding_aids,
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
        parser.add_argument(
            "-s3",
            "--s3-key",
            nargs=1,
            type=str,
            help="s3 key location for storing the bundle",
        )
        parser.add_argument(
            "--force-publish",
            action="store_true",
        )

    def handle(self, *args, **kwargs):
        s3_key = kwargs.get("s3_key")
        repository_id = kwargs.get("repository")
        finding_aid_ids = kwargs.get("finding_aid_ids")
        force_publish = kwargs.get("force_publish")

        if repository_id:
            finding_aids = FindingAid.objects.filter(repository_id=repository_id)
        elif finding_aid_ids:
            finding_aids = FindingAid.objects.filter(id__in=finding_aid_ids)

        self.stdout.write(
            f"Bulk indexing {finding_aids.count()} finding aids",
        )
        bulk_index_finding_aids(
            finding_aids,
            force_publish=force_publish,
            s3_key=s3_key,
        )


def bulk_index_finding_aids(
    finding_aids: QuerySet,
    *,
    force_publish: bool = False,
    s3_key: str | None = None,
):
    if not s3_key:
        now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
        s3_key = f"indexing/bulk/{now_str}"

    for finding_aid in finding_aids:
        finding_aid.queue_status(force_publish=force_publish)

    if settings.ENABLE_AIRFLOW:
        logger.info("bulk indexing %s finding aids", finding_aids.count())
        bulk_prep_finding_aids(finding_aids, s3_key)
        return trigger_dag(
            "bulk_index_finding_aids",
            {"s3_key": s3_key},
            related_models=finding_aids,
            dag_run_prefix=f"{settings.AIRFLOW_PROJECT_NAME}__bulk",
        )
    return "Airflow not enabled"
