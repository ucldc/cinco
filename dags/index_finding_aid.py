from datetime import datetime
from airflow.decorators import dag, task
from airflow.models.param import Param

from cinco.cincoctrl_operator import CincoCtrlOperator
from cinco.arclight_operator import ArcLightOperator


@dag(
    dag_id="index_finding_aid",
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    params={
        "finding_aid_id": Param(
            None, description="The ID of the Finding Aid in CincoCtrl"
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
        finding_aid_id="{{ params.finding_aid_id }}",
        s3_key=s3_key,
        # on_failure_callback=notify_failure,
        # on_success_callback=notify_success
    )
    prepare_finding_aid.set_upstream(s3_key)

    index_finding_aid_task = ArcLightOperator(
        task_id="index_finding_aid",
        finding_aid_id="{{ params.finding_aid_id }}",
        s3_key=s3_key,
        # on_failure_callback=notify_failure,
        # on_success_callback=notify_success
    )

    s3_key >> prepare_finding_aid >> index_finding_aid_task

    # @task()
    # def cleanup_s3():
    #     boto3.client("s3").delete_object(Bucket="", Key=make_s3_key)


index_finding_aid = index_finding_aid()
