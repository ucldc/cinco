"""
The bulk_index_finding_aids dag only has 2 tasks - the arclight indexing
task and the s3 cleanup task. For the arclight indexing task, I was
unable to take the approach where we pass multiple finding aids to the
same traject command, since there are other variables required
(repository id, ark, preview flag). Instead, I wrote a new script that
iterates through all the finding-aid-supplemental-file-indexing-env-bundles
in a given bulk job, and runs the traject command for each one.
"""

import boto3
from datetime import datetime
from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.models import Variable

from cinco.arclight_operator import ArcLightOperator


@dag(
    dag_id="bulk_index_finding_aids",
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    params={
        "s3_key": Param(
            "",
            type="string",
            description="The s3_key where all the indexable finding aids are stored",
        ),
        "cinco_environment": Param(
            "stage",
            enum=["stage", "prd"],
            description="The Arclight environment to run",
        ),
    },
    tags=["cinco"],
    # on_failure_callback=notify_dag_failure,
    # on_success_callback=notify_dag_success,
)
def bulk_index_finding_aids():
    bulk_index_task = ArcLightOperator(
        task_id="bulk_index_task",
        s3_key="{{ params.s3_key }}",
        arclight_command="bulk-index-from-s3",
        cinco_environment="{{ params.cinco_environment }}",
        # on_failure_callback=notify_failure,
        # on_success_callback=notify_success
    )

    @task()
    def cleanup_s3(s3_key, cinco_environment="stage"):
        s3 = boto3.resource("s3")
        if cinco_environment == "prd":
            bucket_name = Variable.get("CINCO_S3_BUCKET_PRD")
        else:
            bucket_name = Variable.get("CINCO_S3_BUCKET_STAGE")
        prefix = f"media/{s3_key}"
        print(f"Deleting objects in {bucket_name} at {prefix}")
        bucket = s3.Bucket(bucket_name)
        delete_results = bucket.objects.filter(Prefix=prefix).delete()
        print(delete_results)

    bulk_index_task >> cleanup_s3(
        "{{ params.s3_key }}", cinco_environment="{{ params.cinco_environment }}"
    )


bulk_index_finding_aids = bulk_index_finding_aids()
