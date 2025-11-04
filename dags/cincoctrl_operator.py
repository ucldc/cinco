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


class CincoCtrlOperatorMixin:
    # Define template fields so Airflow knows to render these
    template_fields = (
        "manage_cmd",
        "finding_aid_id",
        "s3_key",
        "queryset_filters",
        "finding_aid_ark",
        "max_num_records",
        "max_file_size_in_MB",
    )

    def setup_cincoctrl_attributes(
        self,
        manage_cmd,
        cinco_environment=None,
        finding_aid_id=None,
        s3_key=None,
        queryset_filters=None,
        finding_aid_ark=None,
        max_num_records=None,
        max_file_size_in_MB=None,
    ):
        # Store parameters as instance variables for later use in execute()
        self.manage_cmd = manage_cmd
        self.finding_aid_id = finding_aid_id
        self.s3_key = s3_key
        self.queryset_filters = queryset_filters
        self.finding_aid_ark = finding_aid_ark
        self.cinco_environment = cinco_environment
        self.max_num_records = max_num_records
        self.max_file_size_in_MB = max_file_size_in_MB

    def compose_manage_args(self, context):
        """Compose manage args using the rendered template values, only including valid values"""

        def is_not_none(value):
            """Check if a value is not None (handles None, 'None' string, empty, and 'null')"""
            return value is not None and str(value).lower() not in ("none", "", "null")

        manage_args = []

        if self.manage_cmd == "prepare_finding_aid":
            if is_not_none(self.finding_aid_id):
                manage_args.extend(["--finding-aid-id", str(self.finding_aid_id)])
            if is_not_none(self.s3_key):
                manage_args.extend(["--s3-key", str(self.s3_key)])

        elif self.manage_cmd == "bulk_prepare_finding_aids":
            if is_not_none(self.queryset_filters):
                manage_args.extend(["--filters", str(self.queryset_filters)])
            if is_not_none(self.s3_key):
                manage_args.extend(["--s3-key", str(self.s3_key)])
            if is_not_none(self.max_num_records):
                manage_args.extend(["--max-num-records", str(self.max_num_records)])
            if is_not_none(self.max_file_size_in_MB):
                manage_args.extend(
                    ["--max-file-size-in-MB", str(self.max_file_size_in_MB)]
                )
            manage_args.extend(["--dag_run_id", str(context["dag_run"].run_id)])
            manage_args.extend(["--logical_date", str(context["logical_date"])])

        elif self.manage_cmd == "remove_finding_aid":
            if is_not_none(self.finding_aid_ark):
                manage_args.extend(["--ark", str(self.finding_aid_ark)])

        elif self.manage_cmd == "bulk_remove_finding_aids":
            if is_not_none(self.s3_key):
                manage_args.extend(["--s3-key", str(self.s3_key)])

        elif self.manage_cmd == "mark_unpublished":
            if is_not_none(self.finding_aid_ark):
                manage_args.extend(["--ark", str(self.finding_aid_ark)])

        return manage_args


class CincoCtrlEcsOperator(CincoCtrlOperatorMixin, EcsRunTaskOperator):
    def __init__(self, **kwargs):
        # Validate that cinco_environment is provided for ECS operator
        if "cinco_environment" not in kwargs or kwargs["cinco_environment"] is None:
            raise ValueError("cinco_environment is required for CincoCtrlEcsOperator")

        # Extract mixin-specific arguments
        cincoctrl_args = {
            "manage_cmd": kwargs.pop("manage_cmd"),
            "cinco_environment": kwargs.pop("cinco_environment"),
            "finding_aid_id": kwargs.pop("finding_aid_id", None),
            "s3_key": kwargs.pop("s3_key", None),
            "queryset_filters": kwargs.pop("queryset_filters", None),
            "finding_aid_ark": kwargs.pop("finding_aid_ark", None),
            "max_num_records": kwargs.pop("max_num_records", None),
            "max_file_size_in_MB": kwargs.pop("max_file_size_in_MB", None),
        }

        # Set up mixin attributes
        self.setup_cincoctrl_attributes(**cincoctrl_args)

        container_name = f"cinco-ctrl-{self.cinco_environment}-container"
        # TODO: specify task definition revision? how?
        ecs_names = {
            "cluster": f"cinco-{ self.cinco_environment }",
            "task_definition": f"cinco-ctrl-{ self.cinco_environment }",
        }
        args = {
            "launch_type": "FARGATE",
            "platform_version": "LATEST",
            "overrides": {
                "containerOverrides": [
                    {
                        "name": container_name,
                        "command": [
                            "python",
                            "manage.py",
                            self.manage_cmd,
                        ],
                    }
                ]
            },
            "region": "us-west-2",
            "awslogs_group": f"/ecs/cinco-ctrl-{ self.cinco_environment }",
            "awslogs_stream_prefix": f"ecs/cinco-ctrl-{ self.cinco_environment }-container",
            "awslogs_region": "us-west-2",
            "reattach": True,
            "number_logs_exception": 100,
            "waiter_delay": 10,
            "waiter_max_attempts": 8640,
        }
        args.update(ecs_names)
        args.update(kwargs)
        EcsRunTaskOperator.__init__(self, **args)

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
                "securityGroups": [
                    os.environ.get("CINCOCTRL_STAGE_SERVICE_SECURITY_GROUP"),
                    os.environ.get("CINCOCTRL_PRD_SERVICE_SECURITY_GROUP"),
                ],
                "assignPublicIp": "ENABLED",
            }
        }

        # Jinja templates are rendered in execute, so compose manage args here
        manage_args = self.compose_manage_args(context)
        self.overrides["containerOverrides"][0]["command"] = [
            "python",
            "manage.py",
            self.manage_cmd,
            *manage_args,
        ]

        return super().execute(context)


class CincoCtrlDockerOperator(CincoCtrlOperatorMixin, DockerOperator):
    def __init__(self, **kwargs):
        # Extract mixin-specific arguments
        cincoctrl_args = {
            "manage_cmd": kwargs.pop("manage_cmd"),
            "cinco_environment": kwargs.pop("cinco_environment", "dev"),
            "finding_aid_id": kwargs.pop("finding_aid_id", None),
            "s3_key": kwargs.pop("s3_key", None),
            "queryset_filters": kwargs.pop("queryset_filters", None),
            "finding_aid_ark": kwargs.pop("finding_aid_ark", None),
            "max_num_records": kwargs.pop("max_num_records", None),
            "max_file_size_in_MB": kwargs.pop("max_file_size_in_MB", None),
        }

        # Set up mixin attributes
        self.setup_cincoctrl_attributes(**cincoctrl_args)

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
        # aws_conf = "cincoctrl/.envs/.local/.aws"
        env = {
            **dotenv_values(f"{mwaa_local_mount}/{django_conf}"),
            **dotenv_values(f"{mwaa_local_mount}/{postgres_conf}"),
            # **dotenv_values(f"{mwaa_local_mount}/{aws_conf}"),
            **{"POSTGRES_HOST": os.environ.get("CINCO_POSTGRES_HOST", "postgres")},
            **{"CINCO_MINIO_ENDPOINT": os.environ.get("CINCO_MINIO_ENDPOINT", "")},
        }

        container_image = "cincoctrl_local_django"
        container_version = "latest"
        container_name = "cincoctrl_local_django-managepy"

        # Don't include manage_args in the initial command - we'll add them in execute()
        args = {
            "image": f"{container_image}:{container_version}",
            "container_name": container_name,
            "command": [
                "python",
                "manage.py",
                self.manage_cmd,
            ],
            "network_mode": "bridge",
            "auto_remove": "force",
            "mounts": mounts,
            "mount_tmp_dir": False,
            "environment": env,
            "max_active_tis_per_dag": 4,
        }
        args.update(kwargs)
        DockerOperator.__init__(self, **args)

    def execute(self, context):
        # Jinja templates are rendered in execute, so compose manage args here
        manage_args = self.compose_manage_args(context)
        self.command = self.command + manage_args

        print(f"Running {self.command} on {self.image} image")
        print(f"{self.environment=}")

        return super().execute(context)


if CONTAINER_EXECUTION_ENVIRONMENT == "ecs":
    CincoCtrlOperator = CincoCtrlEcsOperator
elif CONTAINER_EXECUTION_ENVIRONMENT == "docker":
    CincoCtrlOperator = CincoCtrlDockerOperator
