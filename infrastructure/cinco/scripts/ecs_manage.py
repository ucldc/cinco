import os
# import time

import boto3


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


def main(command: list[str] = ["migrate"]):
    cinco_ctrl = get_stack("cinco-stage-ctrl")
    cluster = get_stack_output(cinco_ctrl, "ECSCluster")
    task_definition = get_stack_output(cinco_ctrl, "TaskDefinition")
    task_definition = ":".join(task_definition.split(":")[:-1])

    print(f"Running `python manage.py {' '.join(command)}` " "on Cinco Ctrl in ECS")

    ecs_client = boto3.client("ecs", region_name="us-west-2")
    resp = ecs_client.run_task(
        **task_template(),
        cluster=cluster,
        taskDefinition=task_definition,
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": os.environ["SUBNET_IDS"].split(","),
                "securityGroups": [
                    get_stack_output(cinco_ctrl, "ServiceSecurityGroup")
                ],
                "assignPublicIp": "ENABLED",
            }
        },
        overrides={
            "containerOverrides": [
                {
                    "name": "cinco-ctrl-container",
                    "command": ["python", "manage.py", *command],
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
    log_group_name = "/ecs/cinco-ctrl"
    log_stream_name = f"ecs/cinco-ctrl-container/{task_id}"
    print(
        f"aws logs tail --follow {log_group_name} --log-stream-name-prefix "
        f"{log_stream_name} --region us-west-2"
    )

    # events = 0
    # print(f"Retrieving last 50 lines for {container_name}/{task_id}:")
    # while events < 50:
    #     try:
    #         log_resp = cloudwatch.get_log_events(
    #             logGroupName=log_group_name,
    #             logStreamName=log_stream_name,
    #             limit=50,
    #             startFromHead=False,
    #         )
    #     except cloudwatch.exceptions.ResourceNotFoundException:
    #         time.sleep(30)
    #         print("trying again...")
    #         print("or cancel this process and run...")
    #         print(
    #             f"aws logs tail --follow {log_group_name} --log-stream-name-prefix {log_stream_name}"
    #         )
    #         continue

    #     for event in log_resp["events"]:
    #         events += 1
    #         print(event["message"])


# python ecs_manage.py createsuperuser --no-input --email <email>
# python ecs_manage.py migrate --no-input
# python ecs_manage.py collectstatic --no-input
if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
