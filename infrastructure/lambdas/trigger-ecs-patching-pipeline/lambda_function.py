import boto3
from botocore.exceptions import ClientError
import json
import requests


def handler(event, context):
    """
    Trigger a rebuild and redeploy of an ecs service using the code
    version that is currently deployed to the service.

    We determine the commit hash of the currently deployed version
    and then trigger a CodePipeline with a source version override.
    """
    pipeline_name = event["pipeline"]
    cluster = event["cluster"]
    service_name = event["service"]
    git_repo = event["gitrepo"]

    ecs_client = boto3.client("ecs")
    pipeline_client = boto3.client("codepipeline")

    # get latest service deployment
    response = ecs_client.list_service_deployments(
        service=service_name,
        cluster=cluster,
        status=[
            "SUCCESSFUL",
        ],
    )
    latest_deployment = response.get("serviceDeployments")[0]

    # get deployed task definition
    response = ecs_client.describe_service_revisions(
        serviceRevisionArns=[latest_deployment["targetServiceRevisionArn"]]
    )
    service_revision = response["serviceRevisions"][0]
    task_definition_arn = service_revision["taskDefinition"]

    # get docker image name
    response = ecs_client.describe_task_definition(taskDefinition=task_definition_arn)
    image_name = response["taskDefinition"]["containerDefinitions"][0]["image"]

    # get image tag
    # image name format: [REGISTRY_HOST[:REGISTRY_PORT]/][NAMESPACE/]REPOSITORY[:TAG]
    image_tag = None
    image_repo = image_name.split("/")[-1]
    if ":" in image_repo:
        image_tag = image_repo.split(":")[-1]

    # get git commit hash
    commit_hash = None
    if image_tag and image_tag != "latest":
        try:
            url = f"https://api.github.com/repos/{git_repo}/git/ref/tags/{image_tag}"
            response = requests.get(url=url)
            response.raise_for_status()
            commit_hash = response.json()["object"]["sha"]
        except requests.exceptions.HTTPError:
            url = f"https://api.github.com/repos/{git_repo}/commits/{image_tag}"
            response = requests.get(url=url)
            response.raise_for_status()
            commit_hash = response.json()
    else:
        # assume the latest commit to main branch
        url = f"https://api.github.com/repos/{git_repo}/commits/main"
        response = requests.get(url=url)
        response.raise_for_status()
        commit_hash = response.json()["sha"]

    if not commit_hash:
        msg = f"Could not get a git commit hash for image: {image_name}"
        print(msg)
        return {"statusCode": 500, "body": json.dumps({"error": msg})}

    # Trigger the pipeline with overrides
    params = {
        "name": pipeline_name,
        "clientRequestToken": context.aws_request_id,  # Prevents accidental duplicate triggers
        "sourceRevisions": [
            {
                "actionName": "Source",
                "revisionType": "COMMIT_ID",
                "revisionValue": commit_hash,
            }
        ],
    }

    try:
        # Trigger the pipeline
        response = pipeline_client.start_pipeline_execution(**params)
    except ClientError as e:
        print(f"Error starting pipeline: {e.response['Error']['Message']}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    execution_id = response.get("pipelineExecutionId")
    print(
        f"Successfully triggered pipeline {pipeline_name}. Execution ID: {execution_id}"
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Pipeline triggered successfully",
                "pipelineExecutionId": execution_id,
            }
        ),
    }
