from datetime import datetime
from airflow.decorators import dag

from cinco.cincoctrl_operator import CincoCtrlOperator


@dag(
    dag_id="poll_message_queue",
    schedule="*/10 * * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["cinco"],
    # on_failure_callback=notify_dag_failure,
    # on_success_callback=notify_dag_success,
)
def poll_message_queue():
    poll_queue = CincoCtrlOperator(  # noqa: F841
        task_id="poll_queue",
        manage_cmd="poll_sqs",
        cinco_environment="stage",
        trigger_rule="always",
        # on_failure_callback=notify_failure,
        # on_success_callback=notify_success
    )
    # Uncomment when we have production architecture
    # poll_queue_prod = CincoCtrlOperator(
    #     task_id="poll_queue_prod",
    #     manage_cmd="poll_sqs",
    #     cinco_environment="prd",
    #     trigger_rule="always",
    #     # on_failure_callback=notify_failure,
    #     # on_success_callback=notify_success
    # )
    # poll_queue >> poll_queue_prod


poll_message_queue = poll_message_queue()
