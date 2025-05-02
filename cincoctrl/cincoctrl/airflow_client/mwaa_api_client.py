import json
import logging
from datetime import UTC
from datetime import datetime

import boto3
from django.conf import settings

from .exceptions import MWAAAPIError
from .models import PRESERVE_TRIGGER
from .models import JobRun
from .models import JobTrigger

env_name = settings.AIRFLOW_ENV_NAME
env_url = settings.AIRFLOW_ENV_URL
logger = logging.getLogger(__name__)


def mwaa_client(func):
    """
    decorator that creates a client if a client isn't passed in
    """

    def wrapper(*args, **kwargs):
        if "client" in kwargs:
            client = kwargs.pop("client")
            return func(*args, client, **kwargs)
        client = boto3.client("mwaa")
        return func(*args, client, **kwargs)

    return wrapper


@mwaa_client
def trigger_dag(dag, dag_conf, client, related_model=None, dag_run_prefix=None):
    request_params = {
        "Name": env_name,
        "Path": f"/dags/{dag}/dagRuns",
        "Method": "POST",
        "Body": {
            "conf": dag_conf,
            "note": (
                f"Triggered using InvokeRestApi from {settings.AIRFLOW_PROJECT_NAME}"
            ),
        },
    }
    if dag_run_prefix:
        utc_dt = datetime.now(UTC).isoformat()
        request_params["Body"]["dag_run_id"] = f"{dag_run_prefix}__{utc_dt}"
    try:
        resp = client.invoke_rest_api(**request_params)
    except client.exceptions.RestApiServerException as e:
        message = f"Error invoking REST API via boto: {e.response}, {request_params}"
        logger.debug(message)
        resp = e.response
    except client.exceptions.ClientError as e:
        message = f"Error invoking REST API via boto: {e}, {request_params}"
        logger.exception(message)
        raise

    status_code = resp["RestApiStatusCode"]
    dag_run_id = ""
    logical_date = None
    if isinstance(resp["RestApiResponse"], dict):
        dag_run_id = resp["RestApiResponse"].get("dag_run_id")
        logical_date = resp["RestApiResponse"].get("logical_date")
    job_trigger = JobTrigger(
        related_model=related_model,
        dag_id=dag,
        dag_run_conf=json.dumps(dag_conf),
        airflow_url=env_url,
        dag_run_id=dag_run_id,
        logical_date=logical_date,
        rest_api_status_code=status_code,
        rest_api_response=json.dumps(resp),
    )
    job_trigger.save()

    if job_trigger.rest_api_status_code != 200:  # noqa: PLR2004
        raise MWAAAPIError(request_params, status_code, resp["RestApiResponse"])

    return job_trigger


@mwaa_client
def update_job_run(job_trigger, client):
    dag = job_trigger.dag_id
    dag_run_id = job_trigger.dag_run_id

    request_params = {
        "Name": env_name,
        "Path": f"/dags/{dag}/dagRuns/{dag_run_id}",
        "Method": "GET",
    }
    try:
        resp = client.invoke_rest_api(**request_params)
    except client.exceptions.ClientError as e:
        message = f"Error invoking REST API via boto: {e}, {request_params}"
        logger.exception(message)
        raise

    status_code = resp["RestApiStatusCode"]
    if status_code != 200:  # noqa: PLR2004
        raise MWAAAPIError(request_params, status_code, resp["RestApiResponse"])

    job_status = JobRun.RUNNING
    match resp["RestApiResponse"]["state"]:
        case "failed":
            job_status = JobRun.FAILED
        case "success":
            job_status = JobRun.SUCCEEDED

    job_run, created = JobRun.objects.get_or_create(
        related_model=job_trigger.related_model,
        dag_id=dag,
        dag_run_conf=json.dumps(resp["RestApiResponse"].get("conf")),
        airflow_url=env_url,
        dag_run_id=dag_run_id,
        logical_date=resp["RestApiResponse"]["logical_date"],
    )

    if PRESERVE_TRIGGER:
        job_run.job_trigger = job_trigger
    else:
        job_trigger.delete()

    job_run.status = job_status
    job_run.save()


@mwaa_client
def create_variable(client):
    request_params = {
        "Name": env_name,
        "Path": "/variables",
        "Method": "POST",
        "Body": {
            "key": "test-restapi-key",
            "value": "test-restapi-value",
            "description": "Test variable created by MWAA InvokeRestApi API",
        },
    }
    response = client.invoke_rest_api(
        **request_params,
    )

    print("Airflow REST API response: ", response["RestApiResponse"])  # noqa: T201


@mwaa_client
def list_dags(client):
    request_params = {
        "Name": env_name,
        "Path": "/dags",
        "Method": "GET",
        "QueryParameters": {
            "paused": False,
        },
    }
    response = client.invoke_rest_api(
        **request_params,
    )

    print("Airflow REST API response: ", response["RestApiResponse"])  # noqa: T201


if __name__ == "__main__":
    client = boto3.client("mwaa")
    trigger_dag("index_finding_aid", {"finding_aid_id": "2"}, client=client)
    list_dags(client=client)
    create_variable(client=client)
