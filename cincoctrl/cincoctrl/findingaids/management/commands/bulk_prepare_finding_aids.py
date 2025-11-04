"""
Designed to be run from Airflow as the first part of the bulk_index_finding_aids DAG.

To prepare finding aids for indexing in bulk, run:
    python manage.py bulk_prepare_finding_aids

Arguments:
--finding-aid-ids: [optional] a list of finding aid ids to reindex. If any
    filters are provided, the filters will be applied to this list. If no
    finding aid ids are provided, filters will be applied to set of all
    finding aids.
--filters: [optional] one or more filter queries to apply to the finding
    aids specified by --finding-aid-ids, or to all finding aids if no
    finding aid ids are provided. Format is FIELD_LOOKUP=VALUE(S), e.g.,
    --filters repository_id=1 status=published or
    --filters repository_id__in=[1,2,3] status__in=['published','previewed']
    (see Django Queryset filter() documentation for details on field lookups:
    https://docs.djangoproject.com/en/5.2/ref/models/querysets/#filter)
--s3-key: [required] s3 prefix to customize where the job's working
    files are stored in s3, e.g., indexing/bulk/{s3_job_id}/ (stored in
    storages['default'] Media root under /media/)
--max-num-records: [optional] To reduce the indexer's workload and the risk of
    out of memory errors from the Arclight Container, batch record express
    finding aids into batches of this many records. Default is 200.
--max-file-size-in-MB: [optional] To reduce the indexer's workload and the risk
    of out of memory errors from the Arclight Container, batch EAD finding aids
    into batches where the total size of all EAD files in the batch does not
    exceed this threshold (in MB). Default is 50 MB.
--force-publish: [optional] if True, will force publish all previewed finding
    aids being reindexed. Default is False.

Searches for the list of ids (if provided) or all finding aids,
Filters the queryset by the filters provided,
For safety, filters the queryset for status in ['published', 'previewed'],
    Reports any finding aids skipped with other statuses
Batches up this set of finding aids into batches by count for record express
finding aids, and by total EAD file size for EAD finding aids, to reduce the
indexer's workload and risk of out of memory errors.
Prepares an indexer input bundle for each finding aid in each batch and stores
it in s3 at
/media/indexing/bulk/{s3_job_id}/[express|ead]-{batch_index}/{finding_aid_id}/
"""

import ast
import json
import logging

from django.conf import settings
from django.core.exceptions import FieldError
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from cincoctrl.airflow_client.models import JobRun
from cincoctrl.findingaids.management.commands._prepare_for_indexing import (
    prepare_finding_aid,
)
from cincoctrl.findingaids.models import FindingAid

logger = logging.getLogger(__name__)

cli_warning_output_template = (
    "...\n" + (">" * 3) + "\n>>> WARNING: {warning_message}\n" + (">" * 3)
)


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
    help = "Prepare a queryset of finding aids for bulk indexing"

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
                "Assumes a developer is running this and is familiar with "
                "Django Queryset field lookups (see "
                "https://docs.djangoproject.com/en/5.2/ref/models/querysets/#filter)"
            ),
        )
        parser.add_argument(
            "-s3",
            "--s3-key",
            type=str,
            required=True,
            help="s3 job prefix for storing the pages of finding aids being indexed",
        )
        parser.add_argument(
            "--max-num-records",
            nargs="?",
            default=200,
            type=int,
            metavar="max-num-records",
            help="max number of finding aids in each indexing job",
        )
        parser.add_argument(
            "--max-file-size-in-MB",
            nargs="?",
            default=50,  # 50 MB
            type=int,
            metavar="max-file-size-in-MB",
            help=(
                "Batches will be created such that the total size of EAD files in each "
                "batch does not exceed this threshold (in bytes). If not provided, "
                "batching will be performed at a 50 MB threshold."
            ),
        )
        parser.add_argument(
            "--force-publish",
            action="store_true",
        )
        parser.add_argument(
            "--dag_run_id",
            type=str,
            help="Airflow DAG run ID for tracking this job execution",
        )
        parser.add_argument(
            "--logical_date",
            type=str,
            help="Airflow logical date for this job execution",
        )

    def _create_queryset(
        self,
        finding_aid_ids: list[int] | None,
        filters_argument: list[str] | None,
    ) -> QuerySet:
        # create initial queryset limited by finding_aid_ids if provided
        if finding_aid_ids:
            finding_aids = FindingAid.objects.filter(id__in=finding_aid_ids)
            msg = (
                f"Searching: {len(finding_aid_ids):,} finding aids by ID -> "
                f"{finding_aids.count():,} found."
            )
            num_found = f"{finding_aids.count():,}"
        else:
            finding_aids = FindingAid.objects.all()
            msg = "Searching: all finding aids, no finding aid IDs provided."
            num_found = f"all ({finding_aids.count():,})"
        self.stdout.write(msg)

        # apply any provided filters
        filters = {}
        for filter_argument in filters_argument:
            if filter_argument.count("=") != 1:
                raise InvalidFilterError(filter_argument)
            field_lookup, value = filter_argument.split("=")
            field_lookup = field_lookup.strip()
            value = value.strip()
            if value.startswith("["):
                value = ast.literal_eval(value)
            filters[field_lookup] = value
        msg = f"Filtering: {num_found} finding aids for {filters}"
        finding_aids = finding_aids.filter(**filters)
        msg += f" -> {finding_aids.count()} found."
        self.stdout.write(msg)

        # return the queryset
        return finding_aids

    def _refine_queryset_by_status(
        self,
        finding_aids: QuerySet,
        *,
        force_publish: bool,
    ) -> QuerySet:
        published = finding_aids.filter(status="published").count()
        self.stdout.write(f"Reindexing: {published:,} published finding aids\n")

        previewed = finding_aids.filter(status="previewed").count()
        if force_publish:
            self.stdout.write(
                f"Force publishing: {previewed:,} previewed finding aids\n",
            )
        else:
            self.stdout.write(f"Reindexing: {previewed:,} previewed finding aids\n")

        unindexed_statuses = [
            "started",
            "queued_preview",
            "preview_error",
            "queued_publish",
            "publish_error",
            "unpublished",
        ]
        unindexed_counts = finding_aids.filter(status__in=unindexed_statuses).count()
        if unindexed_counts > 0:
            msg = (
                f"{unindexed_counts:,} finding aids with unindexable statuses will be "
                f"skipped. Re-index these individually in the dashboard."
            )
            self.stdout.write(cli_warning_output_template.format(warning_message=msg))
        return finding_aids.filter(status__in=["published", "previewed"])

    def _batch_by_record_count(
        self,
        finding_aids: QuerySet,
        max_num_records: int,
    ) -> list[list[FindingAid]]:
        return [
            finding_aids[i : i + max_num_records]
            for i in range(0, len(finding_aids), max_num_records)
        ]

    def _batch_by_file_size(
        self,
        finding_aids: QuerySet,
        max_file_size: int,
    ) -> tuple[list[list[FindingAid]], list[FindingAid]]:
        # sort in descending order by ead file size - this makes batching
        # idemptotent, presuming the underlying ead file sizes don't change
        # between runs
        finding_aids = finding_aids.order_by("-ead_filesize")

        # each batch is a tuple: the list of finding aids
        # and the total size of their EAD files
        batches = []
        errors = []

        for finding_aid in finding_aids:
            if not finding_aid.ead_file or not finding_aid.ead_file.size:
                errors.append(finding_aid)
                continue
            fa_size = finding_aid.ead_filesize
            # in a for...else statement, the else clause is run when the
            # loop completes without hitting a break statement
            for batch in batches:
                if batch["total_file_size"] + fa_size <= max_file_size:
                    batch["finding_aids"].append(finding_aid)
                    batch["total_file_size"] += fa_size
                    break
            else:
                batches.append(
                    {
                        "finding_aids": [finding_aid],
                        "total_file_size": fa_size,
                    },
                )
        # don't need total file size anymore, just the list of finding aids
        batches = [batch["finding_aids"] for batch in batches]
        return batches, errors

    def _batch_finding_aids(
        self,
        finding_aids: QuerySet,
        max_num_records: int,
        max_file_size: int,
    ) -> list[list[FindingAid]]:
        express_finding_aids = finding_aids.filter(record_type="express")
        ead_finding_aids = finding_aids.filter(record_type="ead")

        self.stdout.write(
            f"Batching {express_finding_aids.count()} record express finding aids "
            f"in {max_num_records} record batches",
        )
        self.stdout.write(
            f"Batching {ead_finding_aids.count()} ead finding aids in {max_file_size} "
            "MB batches",
        )

        max_file_size = max_file_size * 1024 * 1024  # convert MB to bytes
        batched_express_finding_aids = self._batch_by_record_count(
            express_finding_aids,
            max_num_records,
        )
        batched_ead_finding_aids, ead_errors = self._batch_by_file_size(
            ead_finding_aids,
            max_file_size,
        )

        if ead_errors:
            msg = (
                f"{len(ead_errors)} finding aids could not be batched due to missing "
                f"or invalid EAD file size; pks:\n{ead_errors}\nRe-index these "
                "individually after fixing the issue.\n"
            )
            self.stdout.write(cli_warning_output_template.format(warning_message=msg))
        self.stdout.write(
            f"Created {len(batched_express_finding_aids)} express batches and "
            f"{len(batched_ead_finding_aids)} ead batches.",
        )

        return batched_express_finding_aids + batched_ead_finding_aids

    def _create_job_run_record(self, finding_aids, *args, **kwargs):
        # todo: move this to the cincoctrl action that triggers this airflow job?
        if finding_aids and settings.ENABLE_AIRFLOW:
            job_run = JobRun(
                dag_id="bulk_index_finding_aids",
                dag_run_conf=json.dumps(
                    {
                        "queryset_filters": kwargs.get("filters"),
                        "max_num_records": kwargs.get("max_num_records"),
                        "max_file_size_in_MB": kwargs.get("max_file_size_in_MB"),
                        "s3_key": kwargs.get("s3_key"),
                        "cinco_environment": settings.CINCO_ENVIRONMENT,
                    },
                ),
                airflow_url=settings.AIRFLOW_ENV_URL,
                dag_run_id=kwargs.get("dag_run_id"),
                logical_date=kwargs.get("logical_date"),
            )
            job_run.save()
            job_run.related_models.set(finding_aids)

    def handle(self, *args, **kwargs):
        finding_aid_ids = kwargs.get("finding_aid_ids")
        filters_argument = kwargs.get("filters") or []
        msg = "Preparing finding aids for bulk indexing..."
        self.stdout.write(f"...\n{'*'*80}\n{msg.center(80)}\n{'^'*80}")
        try:
            finding_aids = self._create_queryset(finding_aid_ids, filters_argument)
        except InvalidFilterError as e:
            self.stdout.write(str(e))
            return
        except FieldError as e:
            self.stdout.write(f"Error applying filters: {e}")
            return

        force_publish = kwargs.get("force_publish", False)
        finding_aids = self._refine_queryset_by_status(
            finding_aids,
            force_publish=force_publish,
        )

        self._create_job_run_record(finding_aids, *args, **kwargs)

        max_num_records = kwargs.get("max_num_records")
        max_file_size = kwargs.get("max_file_size_in_MB")
        batches = self._batch_finding_aids(finding_aids, max_num_records, max_file_size)

        s3_key = kwargs.get("s3_key")

        self.stdout.write(
            f"Preparing {len(finding_aids)} finding aids for indexing by batch...\n",
        )

        for i, batch in enumerate(batches, start=1):
            self.stdout.write(
                f"Finding Aids batch {i}/{len(batches)}: {len(batch)} finding aids",
            )
            manifest = ["ark, finding_aid_id, record_type, ead_filesize"]
            for finding_aid in batch:
                manifest.append(
                    f"{finding_aid.ark}, {finding_aid.id}, "
                    f"{finding_aid.record_type}, {finding_aid.ead_filesize}",
                )
                finding_aid.queue_status(force_publish=force_publish)
                finding_aid.update_ead_with_supplementary_files()
                prepare_finding_aid(
                    finding_aid,
                    f"{s3_key}/page-{i}/{finding_aid.id}",
                )
            csv_lines = "\n".join(manifest)
            storages["default"].save(
                f"{s3_key}/page-{i}/manifest.csv",
                ContentFile(csv_lines.encode("utf-8")),
            )

        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        msg = (
            f"Prepared {len(finding_aids)} finding aids in {len(batches)} batches "
            f"for indexing at:"
        )
        self.stdout.write(
            f"...\n{'*'*80}\n"
            f"{msg.center(80)}\ns3://{bucket_name}/media/{s3_key}\n"
            f"{'^'*80}",
        )
