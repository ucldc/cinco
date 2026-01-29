from datetime import datetime
from airflow.sdk import dag

from cinco.cincoctrl_operator import CincoCtrlOperator


@dag(
    dag_id="poll_airflow_api",
    schedule="*/5 * * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["cinco"],
    # on_failure_callback=notify_dag_failure,
    # on_success_callback=notify_dag_success,
)
def cinco_poll_airflow_api():
    poll_airflow = CincoCtrlOperator(  # noqa: F841
        task_id="poll_airflow",
        manage_cmd="poll_airflow",
        cinco_environment="stage",
        trigger_rule="always",
        # on_failure_callback=notify_failure,
        # on_success_callback=notify_success
    )
    # Uncomment when we have production architecture
    poll_airflow_from_prod = CincoCtrlOperator(
        task_id="poll_airflow_from_prod",
        manage_cmd="poll_airflow",
        cinco_environment="prd",
        trigger_rule="always",
        # on_failure_callback=notify_failure,
        # on_success_callback=notify_success
    )
    poll_airflow >> poll_airflow_from_prod


cinco_poll_airflow_api = cinco_poll_airflow_api()
