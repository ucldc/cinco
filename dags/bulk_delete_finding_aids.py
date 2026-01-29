import boto3
from datetime import datetime
from airflow.sdk import dag, task, Variable
from airflow.models.param import Param


from cinco.cincoctrl_operator import CincoCtrlOperator
from cinco.arclight_operator import ArcLightOperator


@dag(
    dag_id="bulk_delete_finding_aids",
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    params={
        "s3_key": Param(
            "",
            type="string",
            description="The s3_key where a csv of 'finding aid ark, repository code' pairs to be deleted are stored",
        ),
        "cinco_environment": Param(
            "stage",
            enum=["stage", "prd"],
            description="The CincoCtrl and ArcLight environment to run",
        ),
    },
    tags=["cinco"],
    # on_failure_callback=notify_dag_failure,
    # on_success_callback=notify_dag_success,
)
def bulk_delete_finding_aid():
    bulk_remove_from_index = ArcLightOperator(
        task_id="bulk_remove_from_index",
        arclight_command="bulk-remove-from-solr",
        s3_key="{{ params.s3_key }}",
        cinco_environment="{{ params.cinco_environment }}",
    )

    bulk_remove_from_database = CincoCtrlOperator(
        task_id="bulk_remove_from_database",
        manage_cmd="bulk_remove_finding_aids",
        s3_key="{{ params.s3_key }}",
        cinco_environment="{{ params.cinco_environment }}",
    )

    @task()
    def bulk_remove_static_finding_aids(s3_key, cinco_environment="stage"):
        s3 = boto3.resource("s3")
        if cinco_environment == "prd":
            bucket_name = Variable.get("CINCO_S3_BUCKET_PRD")
        else:
            bucket_name = Variable.get("CINCO_S3_BUCKET_STAGE")

        removals = s3.get_object(Bucket=bucket_name, Key=s3_key)
        removals = removals["Body"].read().decode("utf-8").splitlines()

        for line in removals:
            ark, _ = line.split(",", 1)
            prefix = f"static_findaids/static_findaids/{ark}"
            print(f"Deleting objects in {bucket_name} at {prefix}")
            bucket = s3.Bucket(bucket_name)
            delete_results = bucket.objects.filter(Prefix=prefix).delete()
            print(delete_results)

    (
        bulk_remove_from_index
        >> bulk_remove_from_database
        >> bulk_remove_static_finding_aids(
            "{{ params.s3_key }}",
            cinco_environment="{{ params.cinco_environment }}",
        )
    )


bulk_delete_finding_aid = bulk_delete_finding_aid()
