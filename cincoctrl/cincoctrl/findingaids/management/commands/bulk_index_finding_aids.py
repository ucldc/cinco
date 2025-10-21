"""
To kick off a bulk indexing job, run:
    python manage.py bulk_index_finding_aids

Arguments:
--finding-aid-ids: a list of finding aid ids to index. If any filters
    are provided, the filters will be applied to this list. If no finding
    aid ids are provided, filters will be applied to set of all finding aids.
--filters: [optional] one or more filter queries to apply to the finding
    aids specified by --finding-aid-ids, or to all finding aids if no
    finding aid ids are provided. Format is FIELD_LOOKUP=VALUE(S), e.g.,
    --filters repository_id=1 status=published or
    --filters repository_id__in=[1,2,3] status__in=['published','previewed']
    (see Django Queryset filter() documentation for details on field lookups:
    https://docs.djangoproject.com/en/5.2/ref/models/querysets/#filter)
--s3-key: [optional] s3 key to customize where the job's working
    files are stored, will use {settings.AWS_STORAGE_BUCKET_NAME}/media/
    (defined in django settings), followed by {s3_key}. Default:
    {AWS_STORAGE_BUCKET_NAME}/media/indexing/bulk/{now}
--force-publish: [optional] if True, will force publish all finding aids,
    default is False.

Constructs a queryset from the list of ids or the repository id, sets
the status field on each finding aid, creates the
finding-aid-supplemental-file-indexing-env-bundle for each finding aid,
and triggers the bulk_index_finding_aids dag with the s3 prefix of the
job's working files as the argument.
"""

import ast
import logging
import math
from datetime import UTC
from datetime import datetime

from django.conf import settings
from django.core.exceptions import FieldError
from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from cincoctrl.airflow_client.mwaa_api_client import trigger_dag
from cincoctrl.findingaids.management.commands._prepare_for_indexing import (
    bulk_prep_finding_aids,
)
from cincoctrl.findingaids.models import FindingAid

logger = logging.getLogger(__name__)


class InvalidFilterError(Exception):
    def __init__(self, filter_argument, message=None):
        doc_link = "https://docs.djangoproject.com/en/5.2/ref/models/querysets/#filter"
        default_message = (
            f"Error applying filters: Cannot resolve '{filter_argument}' into a "
            f"FIELD_LOOKUP=VALUE pair\n  See {doc_link} for details on field lookups."
        )
        self.message = message or default_message
        super().__init__(self.message)


class Command(BaseCommand):
    help = (
        "Prepare the specified finding aids for indexing - specify finding "
        "aids by list of ids or a single repository id."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--finding-aid-ids",
            nargs="*",
            default=None,
            type=int,
            metavar="finding-aid-id",
            help="Optional list of Finding Aid IDs to prepare for indexing",
        )
        parser.add_argument(
            "--filters",
            nargs="*",
            default=None,
            type=str,
            metavar="FILTER_FIELD=FILTER_VALUE(S)",
            help=(
                "Set one or more filter queries on finding aid IDs provided, "
                "or on set of all finding aids, e.g., "
                "--filters repository_id=1 status=published or "
                "--filters repository_id__in=[1,2,3] "
                "status__in=['published','previewed']"
            ),
        )
        parser.add_argument(
            "-s3",
            "--s3-key",
            nargs=1,
            type=str,
            help="s3 key location for storing the bundle",
        )
        parser.add_argument(
            "--max-num-records",
            nargs="?",
            default=None,
            type=int,
            metavar="max-num-records",
            help="max number of finding aids in each indexing job",
        )
        parser.add_argument(
            "--force-publish",
            action="store_true",
        )

    def create_queryset(self, finding_aid_ids, filters_argument) -> QuerySet:
        if finding_aid_ids:
            finding_aids = FindingAid.objects.filter(id__in=finding_aid_ids)
            msg = (
                f"Searching: {len(finding_aid_ids)} finding aids by ID -> "
                f"{finding_aids.count()} found."
            )
        else:
            finding_aids = FindingAid.objects.all()
            msg = "Searching: all finding aids, no finding aid IDs provided."
        self.stdout.write(msg)

        filters = {}
        for filter_argument in filters_argument:
            if filter_argument.count("=") != 1:
                raise InvalidFilterError(filter_argument)
            field_lookup, value = filter_argument.split("=")
            if value.startswith("["):
                value = ast.literal_eval(value)
            filters[field_lookup] = value
        msg = f"Filtering: {finding_aids.count()} finding aids for {filters}"
        finding_aids = finding_aids.filter(**filters)
        msg += f" -> {finding_aids.count()} found."
        self.stdout.write(msg)
        return finding_aids

    def handle(self, *args, **kwargs):
        finding_aid_ids = kwargs.get("finding_aid_ids")
        filters_argument = kwargs.get("filters") or []
        try:
            finding_aids = self.create_queryset(finding_aid_ids, filters_argument)
        except InvalidFilterError as e:
            self.stdout.write(str(e))
            return
        except FieldError as e:
            self.stdout.write(f"Error applying filters: {e}")
            return

        s3_key = kwargs.get("s3_key")
        max_num_records = kwargs.get("max_num_records")
        force_publish = kwargs.get("force_publish")

        count = finding_aids.count()
        self.stdout.write(f"{count} finding aids to index.")

        if max_num_records and count > max_num_records:
            id_list = list(finding_aids.values_list("pk", flat=True))
            num_groups = math.ceil(count / max_num_records)
            batch_size = math.ceil(count / num_groups)
            for start in range(0, count, batch_size):
                end = start + batch_size
                batch = FindingAid.objects.filter(pk__in=id_list[start:end])

                self.stdout.write(
                    f"Bulk indexing batch of {batch.count()} finding aids",
                )
                bulk_index_finding_aids(
                    batch,
                    force_publish=force_publish,
                    s3_key=s3_key,
                )
        elif count > 0:
            self.stdout.write(
                f"Bulk indexing {finding_aids.count()} finding aids",
            )
            bulk_index_finding_aids(
                finding_aids,
                force_publish=force_publish,
                s3_key=s3_key,
            )
        else:
            self.stdout.write("No finding aids to index, exiting.")


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
            {
                "s3_key": s3_key,
                "cinco_environment": settings.CINCO_ENVIRONMENT,
            },
            related_models=finding_aids,
            dag_run_prefix=f"{settings.AIRFLOW_PROJECT_NAME}__bulk",
        )
    return "Airflow not enabled"
