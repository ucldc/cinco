import os
import boto3


from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator

from docker.types import Mount

# generally speaking, the CONTAINER_EXECUTION_ENVIRONMENT should always
# be 'ecs' in deployed MWAA and should always be 'docker' in local development.
# if one is working to debug airflow's connection to ecs, though, it may be
# useful to set CONTENT_HARVEST_EXECUTION_ENVIRONMENT to 'ecs' locally.
CONTAINER_EXECUTION_ENVIRONMENT = os.environ.get(
    "CONTAINER_EXECUTION_ENVIRONMENT", "docker"
)


def get_stack_outputs(stack_name):
    """
    get the outputs of a cloudformation stack
    """
    client = boto3.client("cloudformation", region_name="us-west-2")
    cf_outputs = (
        client.describe_stacks(StackName=stack_name)
        .get("Stacks", [{}])[0]
        .get("Outputs", [])
    )
    return {output["OutputKey"]: output["OutputValue"] for output in cf_outputs}


def get_log_group():
    """
    get the log group name for the arclight container
    """
    outputs = get_stack_outputs("cinco-stage-arclight-app")
    return outputs["LogGroup"]


def get_solr_writer_url():
    """
    get the url of the solr writer from the cloudformation stack
    """
    outputs = get_stack_outputs("cinco-stage-solr-solr")
    return f"http://{outputs['LoadBalancerDNS']}/solr/arclight"


def get_awsvpc_config():
    """
    get public subnets and security group from cloudformation stack for use
    with the ContentHarvestEcsOperator to run tasks in an ECS cluster
    """
    cf_outputs = get_stack_outputs("pad-airflow-mwaa")
    awsvpcConfig = {
        "subnets": [cf_outputs["PublicSubnet1"], cf_outputs["PublicSubnet2"]],
        "securityGroups": [cf_outputs["SecurityGroup"]],
        "assignPublicIp": "ENABLED",
    }
    return awsvpcConfig


class ArcLightEcsOperator(EcsRunTaskOperator):
    def __init__(
        self,
        finding_aid_id,
        s3_key,
        repository_code,
        finding_aid_ark,
        preview,
        **kwargs,
    ):
        cluster_name = "cinco-stage"
        task_name = "cinco-arclight-stage"
        container_name = "cinco-arclight-stage-container"

        command = [
            "bin/index-from-s3",
            finding_aid_id,
            s3_key,
            repository_code,
            finding_aid_ark,
            preview,
        ]

        args = {
            "cluster": cluster_name,
            "launch_type": "FARGATE",
            "platform_version": "LATEST",
            "task_definition": task_name,
            "overrides": {
                "containerOverrides": [
                    {
                        "name": container_name,
                        "command": command,
                    }
                ]
            },
            "region": "us-west-2",
            "awslogs_group": f"/ecs/{task_name}",
            "awslogs_stream_prefix": f"ecs/{container_name}",
            "awslogs_region": "us-west-2",
            "reattach": True,
            "number_logs_exception": 100,
            "waiter_delay": 10,
            "waiter_max_attempts": 8640,
        }
        args.update(kwargs)
        super().__init__(**args)

    def execute(self, context):
        # Operators are instantiated once per scheduler cycle per airflow task
        # using them, regardless of whether or not that airflow task actually
        # runs. The ContentHarvestEcsOperator is used by ecs_content_harvester
        # DAG, regardless of whether or not we have proper credentials to call
        # get_awsvpc_config(). Adding network configuration here in execute
        # rather than in initialization ensures that we only call
        # get_awsvpc_config() when the operator is actually run.
        self.network_configuration = {"awsvpcConfiguration": get_awsvpc_config()}
        self.overrides["containerOverrides"][0]["environment"] = [
            {"name": "SOLR_WRITER", "value": get_solr_writer_url()}
        ]
        return super().execute(context)


class ArcLightDockerOperator(DockerOperator):
    def __init__(
        self,
        finding_aid_id,
        s3_key,
        repository_code,
        finding_aid_ark,
        preview,
        **kwargs,
    ):
        mounts = [
            Mount(
                source="/Users/awieliczka/Projects/cinco/arclight/bin",
                target="/rails/bin",
                type="bind",
            )
        ]

        container_image = "cinco-arclight-indexer"
        container_version = "latest"
        container_name = f"cinco-arclight-indexer-{finding_aid_id}"
        command = [
            "bin/index-from-s3",
            finding_aid_id,
            s3_key,
            repository_code,
            finding_aid_ark,
            preview,
        ]
        args = {
            "image": f"{container_image}:{container_version}",
            "container_name": container_name,
            "command": command,
            "network_mode": "bridge",
            "auto_remove": "force",
            "mounts": mounts,
            "mount_tmp_dir": False,
            "environment": {
                "S3_BUCKET": "awieliczka-test-bucket",
                "SOLR_URL": "http://localhost:8983/solr/arclight",
            },
            "max_active_tis_per_dag": 4,
        }
        args.update(kwargs)
        super().__init__(**args)

    def execute(self, context):
        print(f"Running {self.command} on {self.image} image")
        print(f"{self.environment=}")
        return super().execute(context)


if CONTAINER_EXECUTION_ENVIRONMENT == "ecs":
    ArcLightOperator = ArcLightEcsOperator
elif CONTAINER_EXECUTION_ENVIRONMENT == "docker":
    ArcLightOperator = ArcLightDockerOperator
