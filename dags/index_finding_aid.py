import boto3
from datetime import datetime
from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.models import Variable

from cinco.cincoctrl_operator import CincoCtrlOperator
from cinco.arclight_operator import ArcLightOperator


@dag(
    dag_id="index_finding_aid",
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    params={
        "finding_aid_id": Param(
            "", type="integer", description="The ID of the Finding Aid in CincoCtrl"
        ),
        "repository_code": Param(
            "", type="string", description="The repository code for the Finding Aid"
        ),
        "finding_aid_ark": Param(
            "", type="string", description="The ARK of the Finding Aid"
        ),
        "eadid": Param(
            "",
            type="string",
            description="If present the filename in s3 elese the collection number",
        ),
        "preview": Param(
            "publish", type="string", description="Either preview or publish"
        ),
    },
    tags=["cinco"],
    # on_failure_callback=notify_dag_failure,
    # on_success_callback=notify_dag_success,
)
def index_finding_aid():
    @task()
    def make_s3_key(params=None, **context):
        if not params or not params.get("finding_aid_id"):
            raise ValueError("Finding Aid ID not found in params")
        finding_aid_id = params.get("finding_aid_id")
        return f"indexing/{finding_aid_id}/{datetime.now().isoformat()}"

    s3_key = make_s3_key()

    prepare_finding_aid = CincoCtrlOperator(
        task_id="prepare_finding_aid",
        manage_cmd="prepare_finding_aid",
        finding_aid_id="{{ params.finding_aid_id }}",
        s3_key=s3_key,
        # on_failure_callback=notify_failure,
        # on_success_callback=notify_success
    )
    prepare_finding_aid.set_upstream(s3_key)

    index_finding_aid_task = ArcLightOperator(
        task_id="index_finding_aid",
        arclight_command="index-from-s3",
        finding_aid_id="{{ params.finding_aid_id }}",
        s3_key=s3_key,
        repository_code="{{ params.repository_code }}",
        finding_aid_ark="{{ params.finding_aid_ark }}",
        eadid="{{ params.eadid }}",
        preview="{{ params.preview }}",
        # on_failure_callback=notify_failure,
        # on_success_callback=notify_success
    )

    @task()
    def cleanup_s3(s3_key):
        s3 = boto3.resource("s3")
        bucket_name = Variable.get("CINCO_S3_BUCKET")
        prefix = f"media/{s3_key}"
        print(f"Deleting objects in {bucket_name} at {prefix}")
        bucket = s3.Bucket(bucket_name)
        delete_results = bucket.objects.filter(Prefix=prefix).delete()
        print(delete_results)

    s3_key >> prepare_finding_aid >> index_finding_aid_task >> cleanup_s3(s3_key)


index_finding_aid = index_finding_aid()
