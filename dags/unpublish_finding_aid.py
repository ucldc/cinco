from datetime import datetime
from airflow.sdk import dag
from airflow.models.param import Param

from cinco.cincoctrl_operator import CincoCtrlOperator
from cinco.arclight_operator import ArcLightOperator


@dag(
    dag_id="unpublish_finding_aid",
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
def unpublish_finding_aid():
    remove_from_index = ArcLightOperator(
        task_id="remove_from_index",
        arclight_command="remove-from-solr",
        finding_aid_ark="{{ params.finding_aid_ark }}",
        repository_code="{{ params.repository_code }}",
        cinco_environment="{{ params.cinco_environment }}",
    )
    remove_from_index

    mark_unpublished = CincoCtrlOperator(
        task_id="mark_unpublished",
        manage_cmd="mark_unpublished",
        finding_aid_ark="{{ params.finding_aid_ark }}",
        cinco_environment="{{ params.cinco_environment }}",
    )

    remove_from_index >> mark_unpublished


unpublish_finding_aid = unpublish_finding_aid()
