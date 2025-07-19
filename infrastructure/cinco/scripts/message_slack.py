import json
import urllib3
import os
import argparse

http = urllib3.PoolManager()

# set as part of the build environment
AWS_ACCOUNT = os.environ.get("AWS_ACCOUNT_ID", "")
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "")
SLACK_HOOK = os.environ.get("SLACK_HOOK", "")

td_url_template = "https://{aws_account}.{aws_region}.console.aws.amazon.com/ecs/v2/task-definitions/{td_family}/{td_revision}/containers"
service_url_template = "https://{aws_account}.{aws_region}.console.aws.amazon.com/ecs/v2/clusters/cinco-prd/services/{service_name}"


def craft_slack_message(application, cinco_version, family_revision):
    if application == "cincoctrl":
        image = "cinco-ctrl"
        name = "CincoCtrl prd"
    elif application == "arclight":
        image = "arclight"
        name = "Arclight prd"

    td_family = family_revision.split(":")[0]
    td_revision = family_revision.split(":")[1]
    service_name = f"{td_family}-service"

    task_definition_url = td_url_template.format(
        aws_account=AWS_ACCOUNT,
        aws_region=AWS_REGION,
        td_family=td_family,
        td_revision=td_revision,
    )
    service_url = service_url_template.format(
        aws_account=AWS_ACCOUNT, aws_region=AWS_REGION, service_name=service_name
    )

    tasks = f"{service_url}/tasks?region={AWS_REGION}"
    logs = f"{service_url}/logs?region={AWS_REGION}"
    deployments = f"{service_url}/deployments?region={AWS_REGION}"

    button_links = [("Tasks", tasks), ("Logs", logs), ("Deployments", deployments)]
    mrkdwn_message = f"*{name}* - deploying image `{image}:{cinco_version}` ; task definition: <{task_definition_url}|{td_family}:{td_revision}>"

    message = {
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": mrkdwn_message}},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": link[0],
                        },
                        "url": link[1],
                    }
                    for link in button_links
                ],
            },
        ]
    }

    return message


def craft_solr_slack_message(cinco_version, family_revisions):
    """
    Crafts a Slack message for Solr deployments.
    :param cinco_version: Version of Cinco being deployed.
    :param family_revisions: Dictionary with family names as keys and their revisions as values.
    :return: Formatted Slack message.
    """
    rich_text_elements = []
    for family_revision in family_revisions:
        family, revision = family_revision.split(":")
        td_url = td_url_template.format(
            aws_account=AWS_ACCOUNT,
            aws_region=AWS_REGION,
            td_family=family,
            td_revision=revision,
        )
        service_name = f"{family}-service"
        service_url = (
            service_url_template.format(
                aws_account=AWS_ACCOUNT,
                aws_region=AWS_REGION,
                service_name=service_name,
            )
            + "/health?region="
            + AWS_REGION
        )
        rich_text_elements.append(
            {
                "type": "rich_text_section",
                "elements": [
                    {"type": "link", "url": service_url, "text": service_name},
                    {"type": "text", "text": " with task definition "},
                    {"type": "link", "url": td_url, "text": f"{family}:{revision}"},
                ],
            }
        )

    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*CincoSolr prd* - built image `cinco-solr:{cinco_version}` and created task definition revisions.\nPlease update the following services (one at a time, in the following order):",
                },
            },
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_list",
                        "style": "bullet",
                        "indent": 0,
                        "elements": rich_text_elements,
                    }
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Indexing will pause during update of cinco-solr-prd-service*",
                },
            },
        ]
    }


def main(application, cinco_version, td_family_revisions):
    try:
        if application == "solr":
            message = craft_solr_slack_message(cinco_version, td_family_revisions)
            icon_emoji = ":solr:"
        else:
            message = craft_slack_message(
                application, cinco_version, td_family_revisions[0]
            )
            icon_emoji = ":hammer_and_wrench:"

        data = {
            "channel": "#oac5",
            "username": "aws-codebuild",
            "icon_emoji": icon_emoji,
            "blocks": message["blocks"],
            "unfurl_links": False,
            "unfurl_media": False,
        }

        resp = http.request("POST", SLACK_HOOK, body=json.dumps(data).encode("utf-8"))
    except Exception as e:
        print({"error": f"Slack notification failed: {e}"})
        return

    print(
        {
            "message": message,
            "status_code": resp.status,
            "response": resp.data,
        }
    )


if __name__ == "__main__":
    # add cinco_version, td_revision as required arguments to the script
    parser = argparse.ArgumentParser(
        description="Send a slack notification on deployment"
    )

    parser.add_argument(
        "--application",
        type=str,
        required=True,
        help="Application that was deployed: cincoctrl, arclight, or solr",
    )
    parser.add_argument(
        "--cinco_version",
        type=str,
        required=True,
        help="Cinco version that was deployed",
    )
    parser.add_argument(
        "--td_family_revisions",
        nargs="+",
        required=True,
        help="Any task definition family revisions that were created",
    )

    try:
        args = parser.parse_args()
        application = args.application
        cinco_version = args.cinco_version
        td_family_revisions = args.td_family_revisions
        main(application, cinco_version, td_family_revisions)
    except Exception as e:
        print({"error": f"Argument parsing failed: {e}"})
