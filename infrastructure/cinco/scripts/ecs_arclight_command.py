import os
import argparse

import boto3


def get_stack_output(stack, key):
    stack_outputs = stack["Outputs"]
    for stack_output in stack_outputs:
        if stack_output["OutputKey"] == key:
            return stack_output["OutputValue"]


def get_stack(stack_name: str):
    # get cluster, security groups from arclight stack
    cloudformation = boto3.client("cloudformation", region_name="us-west-2")
    resp = cloudformation.describe_stacks(StackName=stack_name)
    return resp["Stacks"][0]


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


def main(stack: str, command: str, task_definition_revision: int = None):
    stack_name = (
        "cinco-prd-arclight-app" if stack == "prd" else "cinco-stage-arclight-app"
    )
    arclight = get_stack(stack_name)
    cluster = get_stack_output(arclight, "ECSCluster")
    task_definition = get_stack_output(arclight, "TaskDefinition")
    # Remove revision if present
    task_definition = ":".join(task_definition.split(":")[:-1])
    if task_definition_revision is not None:
        task_definition = f"{task_definition}:{task_definition_revision}"

    print(f"Running `bin/{command}` on Arclight in ECS")

    ecs_client = boto3.client("ecs", region_name="us-west-2")
    resp = ecs_client.run_task(
        **task_template(),
        cluster=cluster,
        taskDefinition=task_definition,
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": os.environ["SUBNET_IDS"].split(","),
                "securityGroups": [get_stack_output(arclight, "ServiceSecurityGroup")],
                "assignPublicIp": "ENABLED",
            }
        },
        overrides={
            "containerOverrides": [
                {
                    "name": f"cinco-arclight-{stack}-container",
                    "command": [f"bin/{command}"],
                }
            ]
        },
    )
    task_arn = [task["taskArn"] for task in resp["tasks"]][0]

    print("Waiting until task has stopped...")
    print(task_arn)
    waiter = ecs_client.get_waiter("tasks_stopped")
    try:
        waiter.wait(
            cluster=cluster,
            tasks=[task_arn],
            WaiterConfig={"Delay": 10, "MaxAttempts": 120},
        )
    except Exception as e:
        print("Tasks failed to finish running.", e)
    else:
        print("Tasks finished running.")

    task = ecs_client.describe_tasks(
        cluster=cluster, tasks=[task_arn], include=["TAGS"]
    )["tasks"][0]

    container = task["containers"][0]
    container_name = container["name"]
    exit_code = container["exitCode"]
    if exit_code != 0:
        print(f"ERROR: {container_name} had exit code {exit_code}!")
    else:
        print(f"{container_name} ran successfully!")

    # cloudwatch = boto3.client("logs", region_name="us-west-2")
    task_id = task_arn.split("/")[-1]
    log_group_name = f"/ecs/cinco-arclight-{stack}"
    log_stream_name = f"ecs/cinco-arclight-{stack}-container/{task_id}"
    return (
        f"aws logs tail {log_group_name} --log-stream-name-prefix "
        f"{log_stream_name} --region us-west-2"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run arclight commands on ECS.")
    parser.add_argument(
        "--prd", action="store_true", help="Use the production environment"
    )
    parser.add_argument(
        "--task-definition",
        type=int,
        default=None,
        help="Task definition revision to use (default: latest)",
    )
    parser.add_argument(
        "command", nargs=argparse.REMAINDER, help="Command to run, e.g. index-from-s3"
    )

    args = parser.parse_args()

    stack = "prd" if args.prd else "stage"

    if not args.command:
        parser.error("You must provide an arclight command to run.")

    tail_logs = main(stack, args.command, args.task_definition)
    print(f"{bcolors.OKCYAN}[ECS_MANAGE]: {tail_logs}{bcolors.ENDC}")
    os.system(tail_logs)
