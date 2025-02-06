import os
import boto3

from dotenv import dotenv_values

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
PAD_AIRFLOW_STACK = "pad-airflow-mwaa"


def get_stack_output(stack, key):
    stack_outputs = stack["Outputs"]
    for stack_output in stack_outputs:
        if stack_output["OutputKey"] == key:
            return stack_output["OutputValue"]


def get_stack(stack_name: str):
    # get cluster, security groups from cinco_ctrl stack
    cloudformation = boto3.client("cloudformation", region_name="us-west-2")
    resp = cloudformation.describe_stacks(StackName=stack_name)
    return resp["Stacks"][0]


class CincoCtrlEcsOperator(EcsRunTaskOperator):
    def __init__(self, manage_cmd, finding_aid_id=None, s3_key=None, **kwargs):
        manage_args = []
        if manage_cmd == "prepare_finding_aid":
            manage_args = [finding_aid_id, s3_key]

        container_name = "cinco-ctrl-stage-container"
        args = {
            "cluster": "cinco-stage",
            "launch_type": "FARGATE",
            "platform_version": "LATEST",
            "task_definition": "cinco-ctrl-stage",
            "overrides": {
                "containerOverrides": [
                    {
                        "name": container_name,
                        "command": [
                            "python",
                            "manage.py",
                            manage_cmd,
                            *manage_args,
                        ],
                    }
                ]
            },
            "region": "us-west-2",
            # "awslogs_group": "/ecs/cinco-ctrl-stage",
            # "awslogs_region": "us-west-2",
            # "awslogs_stream_prefix": f"ecs-manage-{manage_cmd}-",
            # "reattach": True,
            # "number_logs_exception": 100,
            # "waiter_delay": 10,
            # "waiter_max_attempts": 8640,
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

        pad_airflow = get_stack(PAD_AIRFLOW_STACK)

        self.network_configuration = {
            "awsvpcConfiguration": {
                "subnets": [
                    get_stack_output(pad_airflow, "PublicSubnet1"),
                    get_stack_output(pad_airflow, "PublicSubnet2"),
                ],
                "securityGroups": [os.environ.get("CINCOCTRL_SECURITY_GROUP")],
                "assignPublicIp": "ENABLED",
            }
        }
        return super().execute(context)


class CincoCtrlDockerOperator(DockerOperator):
    def __init__(self, manage_cmd, finding_aid_id=None, s3_key=None, **kwargs):
        manage_args = []
        if manage_cmd == "prepare_finding_aid":
            manage_args = [finding_aid_id, s3_key]

        # set in startup.sh, path to cinco/cincoctrl on local
        if os.environ.get("CINCO_MOUNT_CINCOCTRL"):
            mounts = [
                Mount(
                    source=os.environ.get("CINCO_MOUNT_CINCOCTRL"),
                    target="/app",
                    type="bind",
                )
            ]
        else:
            mounts = None

        # load environment variables from cincoctrl application
        mwaa_local_mount = f"{os.environ.get('AIRFLOW_HOME')}/local_storage/"
        django_conf = "cincoctrl/.envs/.local/.django"
        postgres_conf = "cincoctrl/.envs/.local/.postgres"
        aws_conf = "cincoctrl/.envs/.local/.aws"
        env = {
            **dotenv_values(f"{mwaa_local_mount}/{django_conf}"),
            **dotenv_values(f"{mwaa_local_mount}/{postgres_conf}"),
            **dotenv_values(f"{mwaa_local_mount}/{aws_conf}"),
            **{"POSTGRES_HOST": os.environ.get("CINCO_POSTGRES_HOST", "")},
        }

        container_image = "cincoctrl_local_django"
        container_version = "latest"
        container_name = f"cincoctrl_local_django-{manage_cmd}-{'-'.join(manage_args)}"

        args = {
            "image": f"{container_image}:{container_version}",
            "container_name": container_name,
            "command": [
                "python",
                "manage.py",
                manage_cmd,
                *manage_args,
            ],
            "network_mode": "bridge",
            "auto_remove": "force",
            "mounts": mounts,
            "mount_tmp_dir": False,
            "environment": env,
            "max_active_tis_per_dag": 4,
        }
        args.update(kwargs)
        super().__init__(**args)

    def execute(self, context):
        print(f"Running {self.command} on {self.image} image")
        print(f"{self.environment=}")
        return super().execute(context)


if CONTAINER_EXECUTION_ENVIRONMENT == "ecs":
    CincoCtrlOperator = CincoCtrlEcsOperator
elif CONTAINER_EXECUTION_ENVIRONMENT == "docker":
    CincoCtrlOperator = CincoCtrlDockerOperator
