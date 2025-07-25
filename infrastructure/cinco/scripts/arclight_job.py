"""
Requires a python3 environment w/ boto3 installed, cdl-pad-prd profile
configured (as per cdl-ssm-util), and AWS_* environment variables.

Runs an ephemeral arclight worker container (outside the ALB) in the
cinco-stage cluster (by default). Pass --prd to run an arclight worker
container in the cinco-prd cluster.

Prints the Task ARN, an aws cli command to tail the logs, an aws cli
command to start an interactive session on the container, and an aws cli
command to stop the container. It does take ~ a minute for the task to
become accessible via `ecs execute-command` (or via the `session`
utility).

By default, the arclight worker container is defined by the same task
definition as the currently running service definition (ie: if the
cinco-arclight-stage-service is running task definition verion 6, then
this script will run a task using task definition version 6).

You can also explicitly specify a task definition revision by passing
--task-definition <revision number>, or use the --latest flag to run the
most recent active task definition revision. (Explicitly specifying
revision number is useful when chained together with task definition
updates in the build pipeline, for example.)

You must specify a command to run on the ephemeral container.

usage examples:

to run a rake command in cinco-stage cluster:
    python arclight_job.py rake ...

to manually index from s3 in cinco-prd cluster:
    python arclight_job.py --prd bin/index-from-s3 <finding_aid_id> <s3_key> <repository_code> <finding_aid_ark> [--preview]"

to build static finding aids in cinco-prd cluster:
    python arclight_job.py --prd bin/build-static-findaids

to examine and explore the filesystem for an older arclight version:
    python arclight_job.py --task-definition 4 sh -c "tail -f /dev/null"
"""

import argparse
import boto3


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


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


def get_solr_leader_url(env="stage"):
    """
    get the url of the solr leader from the cloudformation stack
    """
    outputs = get_stack_outputs(f"cinco-{env}-solr-solr")
    return f"http://{outputs['LoadBalancerDNS']}/solr/arclight"


def task_template():
    return {
        "capacityProviderStrategy": [
            {"capacityProvider": "FARGATE", "weight": 1, "base": 1},
        ],
        "count": 1,
        "platformVersion": "LATEST",
        "enableECSManagedTags": True,
        "enableExecuteCommand": True,
        "startedBy": "arclight_job.py",
    }


def get_service(cluster, env):
    ecs_client = boto3.client("ecs", region_name="us-west-2")
    arclight_service = ecs_client.describe_services(
        cluster=cluster,
        services=[f"cinco-arclight-{env}-service"],
    )
    if arclight_service["failures"]:
        print("Error retrieving ECS service for Arclight:")
        print(arclight_service["failures"])
        raise ValueError(f"No service found for {env} environment.")
    return arclight_service["services"][0]


def get_task_definition(
    cluster, env, task_definition_revision=None, latest: bool = False
):
    # if the task definition's revision number is explicitly specified, use that
    # if --latest flag is specified, run using the latest ACTIVE task_definition
    # otherwise, run this task using the same task definition as the arclight
    # service.

    # In services, when a task definition is updated (to deploy a new image
    # version, for example), the service returns that new task definition
    # revision, even if the deployment is still rolling out, so calling this
    # script directly after a service update will still use the service's
    # most recently specified task definition revision.

    td_family = "cinco-arclight-prd" if env == "prd" else "cinco-arclight-stage"

    if task_definition_revision is not None:
        task_definition = f"{td_family}:{task_definition_revision}"
        return task_definition
    elif latest:
        return td_family
    else:
        arclight_service = get_service(cluster, env)
        task_definition = arclight_service["taskDefinition"]
        return task_definition.split("/")[-1]


def get_service_network_config(cluster, env):
    arclight_service = get_service(cluster, env)
    network_config = arclight_service["networkConfiguration"]
    return network_config


def main(
    env: str,
    command: list[str],
    task_definition_revision: int = None,
    latest: bool = False,
):
    cluster = "cinco-prd" if env == "prd" else "cinco-stage"
    task_definition = get_task_definition(
        cluster, env, task_definition_revision, latest
    )
    network_configuration = get_service_network_config(cluster, env)

    print(f"Running `{' '.join(command)}` on Cinco Arclight {env} in ECS\n")

    ecs_client = boto3.client("ecs", region_name="us-west-2")
    resp = ecs_client.run_task(
        **task_template(),
        cluster=cluster,
        taskDefinition=task_definition,
        networkConfiguration=network_configuration,
        overrides={
            "containerOverrides": [
                {
                    "name": f"cinco-arclight-{env}-container",
                    "command": [*command],
                    "environment": [
                        {
                            "name": "SOLR_URL",
                            "value": get_solr_leader_url(env),
                        }
                    ],
                    "memory": 2048,
                }
            ]
        },
    )
    task_arn = [task["taskArn"] for task in resp["tasks"]][0]
    print(
        f"{bcolors.HEADER}Started task:{bcolors.ENDC} {bcolors.BOLD}{task_arn}{bcolors.ENDC}\n"
    )

    task_id = task_arn.split("/")[-1]
    log_group_name = f"/ecs/cinco-arclight-{stack}"
    log_stream_name = f"ecs/cinco-arclight-{stack}-container/{task_id}"
    print(
        f"{bcolors.HEADER}Tail logs with command:{bcolors.ENDC}\n"
        f"aws logs tail {log_group_name} --log-stream-name-prefix "
        f"{log_stream_name}\n"
    )

    print(
        f"{bcolors.HEADER}Session to the machine with command: (assuming you have a cdl-pad-prd profile){bcolors.ENDC}\n"
        f"aws ecs execute-command --profile cdl-pad-prd "
        f"--cluster arn:aws:ecs:us-west-2:777968769372:cluster/cinco-{env} "
        f"--task {task_arn} "
        f"--container cinco-arclight-{env}-container "
        f"--command /bin/bash --interactive\n"
    )

    print(
        f"{bcolors.HEADER}Stop container with command:{bcolors.ENDC}\n"
        f"aws ecs stop-task --cluster cinco-{env} --task {task_arn}\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run commands on an Arclight ECS instance"
    )
    parser.add_argument(
        "--prd", action="store_true", help="Use the production environment"
    )
    parser.add_argument(
        "--latest", action="store_true", help="Force using the latest task definition"
    )
    parser.add_argument(
        "--task-definition",
        type=int,
        default=None,
        help="Task definition revision to use (default: same as running service)",
    )
    parser.add_argument(
        "command", nargs=argparse.REMAINDER, help="Command to pass to manage.py"
    )

    args = parser.parse_args()

    stack = "prd" if args.prd else "stage"
    latest = True if args.latest else False

    if not args.command:
        parser.error("You must provide a command to run.")

    main(stack, args.command, args.task_definition, latest)
