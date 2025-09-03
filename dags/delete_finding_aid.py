import boto3
from datetime import datetime
from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.models import Variable


from cinco.cincoctrl_operator import CincoCtrlOperator
from cinco.arclight_operator import ArcLightOperator


@dag(
    dag_id="delete_finding_aid",
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    params={
        "finding_aid_ark": Param(
            "", type="string", description="The ARK of the Finding Aid"
        ),
        "repository_code": Param(
            "", type="string", description="The code of the repository"
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
def delete_finding_aid():
    remove_from_index = ArcLightOperator(
        task_id="remove_from_index",
        arclight_command="remove-from-solr",
        finding_aid_ark="{{ params.finding_aid_ark }}",
        repository_code="{{ params.repository_code }}",
        cinco_environment="{{ params.cinco_environment }}",
    )

    remove_from_database = CincoCtrlOperator(
        task_id="remove_from_database",
        manage_cmd="remove_finding_aid",
        finding_aid_ark="{{ params.finding_aid_ark }}",
        cinco_environment="{{ params.cinco_environment }}",
    )

    @task()
    def remove_static_finding_aid(ark, cinco_environment="stage"):
        s3 = boto3.resource("s3")
        if cinco_environment == "prd":
            bucket_name = Variable.get("CINCO_S3_BUCKET_PRD")
        else:
            bucket_name = Variable.get("CINCO_S3_BUCKET_STAGE")

        prefix = f"static_findaids/static_findaids/{ark}"
        print(f"Deleting objects in {bucket_name} at {prefix}")
        bucket = s3.Bucket(bucket_name)
        delete_results = bucket.objects.filter(Prefix=prefix).delete()
        print(delete_results)

    (
        remove_from_index
        >> remove_from_database
        >> remove_static_finding_aid(
            "{{ params.finding_aid_ark }}",
            cinco_environment="{{ params.cinco_environment }}",
        )
    )


delete_finding_aid = delete_finding_aid()
