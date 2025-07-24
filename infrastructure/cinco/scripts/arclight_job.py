import argparse
# import time

import boto3


def task_template():
    return {
        "capacityProviderStrategy": [
            {"capacityProvider": "FARGATE", "weight": 1, "base": 1},
        ],
        "count": 1,
        "platformVersion": "LATEST",
        "enableECSManagedTags": True,
        "enableExecuteCommand": True,
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

    print(f"Running `{' '.join(command)}` on Cinco Arclight {env} in ECS")

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
                    "memory": 2048,
                }
            ]
        },
    )
    task_arn = [task["taskArn"] for task in resp["tasks"]][0]
    print(f"Started task: {task_arn}")

    task_id = task_arn.split("/")[-1]
    log_group_name = f"/ecs/cinco-arclight-{stack}"
    log_stream_name = f"ecs/cinco-arclight-{stack}-container/{task_id}"
    print(
        "Tail logs with command:\n"
        f"aws logs tail {log_group_name} --log-stream-name-prefix "
        f"{log_stream_name} --region us-west-2"
    )

    print(
        f"Session to the machine with command: (assuming you have a cdl-pad-prd profile)\n"
        f"aws ecs execute-command --profile cdl-pad-prd "
        f"--cluster arn:aws:ecs:us-west-2:777968769372:cluster/cinco-{env} "
        f"--task {task_arn} "
        f"--container cinco-arclight-{env}-container "
        "--command /bin/bash --interactive"
    )


# python arclight_job.py rake
# python arclight_job.py bin/generate_static_pages
# python arclight_job.py sh -c tail -f /dev/null
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
    # tail_logs = main(stack, args.command, args.task_definition)
    # print(f"{bcolors.OKCYAN}[ECS_MANAGE]: {tail_logs}{bcolors.ENDC}")
    # os.system(tail_logs)
