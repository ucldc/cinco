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
        )
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
        # on_failure_callback=notify_failure,
        # on_success_callback=notify_success
    )

    @task()
    def cleanup_s3():
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(Variable.get("CINCO_S3_BUCKET"))
        bucket.objects.filter(Prefix="media/{{ params.s3_key }}").delete()

    bulk_index_task >> cleanup_s3()


bulk_index_finding_aids = bulk_index_finding_aids()
