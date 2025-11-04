"""
The bulk_index_finding_aids dag only has 2 tasks - the arclight indexing
task and the s3 cleanup task. For the arclight indexing task, I was
unable to take the approach where we pass multiple finding aids to the
same traject command, since there are other variables required
(repository id, ark, preview flag). Instead, I wrote a new script that
iterates through all the finding-aid-supplemental-file-indexing-env-bundles
in a given bulk job, and runs the traject command for each one.
"""

import os
import uuid
import boto3
from datetime import datetime
from airflow.decorators import dag, task, task_group
from airflow.models.param import Param
from airflow.models import Variable

from cinco.arclight_operator import ArcLightOperator
from cinco.cincoctrl_operator import CincoCtrlOperator


@dag(
    dag_id="bulk_index_finding_aids",
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    params={
        "queryset_filters": Param(
            type="string",
            description="The queryset filters to select Finding Aids to index",
        ),
        "max_num_records": Param(
            type=["integer", "null"],
            description="Threshold number of express records per batch - default 200",
        ),
        "max_file_size_in_MB": Param(
            type=["integer", "null"],
            description="Threshold size of ead files per batch in MB - default 50",
        ),
        "s3_key": Param(
            type=["string", "null"],
            description="The s3 prefix for this bulk indexing job",
        ),
        "cinco_environment": Param(
            "stage",
            enum=["stage", "prd"],
            description="The CincoCtrl and Arclight environment to run",
        ),
    },
    tags=["cinco"],
    # on_failure_callback=notify_dag_failure,
    # on_success_callback=notify_dag_success,
)
def bulk_index_finding_aids():
    @task()
    def make_s3_key(params=None, **context):
        s3_prefix = params.get("s3_key") or str(uuid.uuid4())
        s3_key = f"indexing/bulk/{s3_prefix}"
        return s3_key

    s3_key = make_s3_key()

    bulk_prepare_finding_aids_task = CincoCtrlOperator(
        task_id="bulk_prepare_finding_aids_task",
        manage_cmd="bulk_prepare_finding_aids",
        queryset_filters="{{ params.queryset_filters }}",
        s3_key=s3_key,
        max_num_records="{{ params.max_num_records }}",
        max_file_size_in_MB="{{ params.max_file_size_in_MB }}",
        cinco_environment="{{ params.cinco_environment }}",
        # on_failure_callback=notify_failure,
        # on_success_callback=notify_success
    )

    @task()
    def get_batches_of_finding_aids(s3_key, cinco_environment="stage"):
        CINCO_MINIO_ENDPOINT = os.environ.get("CINCO_MINIO_ENDPOINT", None)
        if CINCO_MINIO_ENDPOINT:
            s3 = boto3.client(
                "s3",
                endpoint_url=CINCO_MINIO_ENDPOINT,
                aws_access_key_id="minioadmin",
                aws_secret_access_key="minioadmin",
                region_name="us-east-1",
            )
        else:
            s3 = boto3.client("s3")
        if cinco_environment == "prd":
            bucket_name = Variable.get("CINCO_S3_BUCKET_PRD")
        else:
            bucket_name = Variable.get("CINCO_S3_BUCKET_STAGE")
        finding_aid_batches = s3.list_objects_v2(
            Bucket=bucket_name, Prefix=f"media/{s3_key}/", Delimiter="/"
        )
        batches = finding_aid_batches.get("CommonPrefixes", [])
        return [
            batch.get("Prefix").replace("media/", "").strip("/") for batch in batches
        ]

    @task_group(group_id="bulk_indexing_and_s3_cleanup")
    def bulk_indexing_and_s3_cleanup(batch_s3_key):
        bulk_index_task = ArcLightOperator(
            task_id="bulk_index_task",
            s3_key=batch_s3_key,
            arclight_command="bulk-index-from-s3",
            cinco_environment="{{ params.cinco_environment }}",
            # on_failure_callback=notify_failure,
            # on_success_callback=notify_success
        )

        @task()
        def cleanup_s3(batch_s3_key, cinco_environment="stage"):
            s3 = boto3.resource("s3")
            if cinco_environment == "prd":
                bucket_name = Variable.get("CINCO_S3_BUCKET_PRD")
            else:
                bucket_name = Variable.get("CINCO_S3_BUCKET_STAGE")
            prefix = f"media/{batch_s3_key}"
            print(f"Deleting objects in {bucket_name} at {prefix}")
            bucket = s3.Bucket(bucket_name)
            delete_results = bucket.objects.filter(Prefix=prefix).delete()
            print(delete_results)

        bulk_index_task >> cleanup_s3(
            batch_s3_key, cinco_environment="{{ params.cinco_environment }}"
        )

    bulk_prepare_finding_aids_task.set_upstream(s3_key)

    finding_aid_batches = get_batches_of_finding_aids(
        s3_key=s3_key, cinco_environment="{{ params.cinco_environment }}"
    )

    (
        bulk_prepare_finding_aids_task
        >> finding_aid_batches
        >> bulk_indexing_and_s3_cleanup.expand(batch_s3_key=finding_aid_batches)
    )


bulk_index_finding_aids = bulk_index_finding_aids()
