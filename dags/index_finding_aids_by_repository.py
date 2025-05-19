from datetime import datetime
from airflow.decorators import dag, task
from airflow.models.param import Param

from cinco.cincoctrl_operator import CincoCtrlOperator
from cinco.arclight_operator import ArcLightOperator


@dag(
    dag_id="index_finding_aids_by_repository",
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    params={
        "repository_id": Param(
            "", type="string", description="The repository id in CincoCtrl"
        )
    },
    tags=["cinco"],
    # on_failure_callback=notify_dag_failure,
    # on_success_callback=notify_dag_success,
)
def index_finding_aids_by_repository():
    @task()
    def make_s3_key(params=None, **context):
        return f"indexing/bulk/{context["task"].dag_run.run_id}"

    s3_key = make_s3_key()

    bulk_prep_task = CincoCtrlOperator(
        task_id="bulk_prep_task",
        manage_cmd="bulk_prep_finding_aids",
        repository_id="{{ params.repository_id }}",
        s3_key=s3_key,
        # on_failure_callback=notify_failure,
        # on_success_callback=notify_success
    )
    bulk_prep_task.set_upstream(s3_key)

    bulk_index_task = ArcLightOperator(
        task_id="bulk_index_task",
        s3_key=s3_key,
        arclight_command="bin/bulk-index-from-s3",
        # on_failure_callback=notify_failure,
        # on_success_callback=notify_success
    )

    s3_key >> bulk_prep_task >> bulk_index_task

    # @task()
    # def cleanup_s3():
    #     boto3.client("s3").delete_object(Bucket="", Key=make_s3_key)


index_finding_aids_by_repository = index_finding_aids_by_repository()
