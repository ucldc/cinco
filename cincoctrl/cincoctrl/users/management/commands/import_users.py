import datetime
import json
from pathlib import Path

import boto3
from django.core.management.base import BaseCommand

from cincoctrl.users.models import Repository
from cincoctrl.users.models import User
from cincoctrl.users.models import UserRole


class Command(BaseCommand):
    """Import users and user roles fixture based on an oac4 db dump"""

    help = "Import users and userroles for an oac4 db dump"

    def add_arguments(self, parser):
        parser.add_argument(
            "oac_dump_filepath",
            help="the location of the oac4 oac dump",
            type=str,
        )

        parser.add_argument(
            "auth_dump_filepath",
            help="the location of the oac4 auth dump",
            type=str,
        )

        parser.add_argument(
            "-b",
            "--bucket",
            help="s3 bucket to fetch from",
            type=str,
        )

    def handle(self, *args, **options):  # noqa: C901, PLR0912
        oac_dump_filepath = options.get("oac_dump_filepath")
        auth_dump_filepath = options.get("auth_dump_filepath")

        bucket = options.get("bucket", False)

        if bucket:
            client = boto3.client("s3")
            oac_obj = client.get_object(Bucket=bucket, Key=oac_dump_filepath)
            oac_data = json.loads(oac_obj["Body"].read())

            auth_obj = client.get_object(Bucket=bucket, Key=auth_dump_filepath)
            auth_data = json.loads(auth_obj["Body"].read())
        else:
            with Path(oac_dump_filepath).open("r") as f:
                oac_data = json.load(f)
            with Path(auth_dump_filepath).open("r") as f:
                auth_data = json.load(f)

        voro_institutions = {}
        voro_group_to_institution = {}
        for record in oac_data:
            if record["model"] == "oac.institution":
                pk = record["pk"]
                voro_institutions[pk] = record["fields"]["cdlpath"]
            elif record["model"] == "oac.groupprofile":
                group_pk = record["fields"]["group"]
                voro_group_to_institution[group_pk] = record["fields"]["institutions"]

        voro_users = []
        voro_groups = {}
        for record in auth_data:
            if record["model"] == "auth.user":
                voro_users.append(record)
            elif record["model"] == "auth.group":
                pk = record["pk"]
                voro_groups[pk] = record["fields"]["name"]

        emails = []
        for voro_user in voro_users:
            voro_user_fields = voro_user["fields"]
            email = voro_user_fields["email"]
            if email and not email in emails:
                emails.append(voro_user_fields["email"])

                last_login = datetime.datetime.fromisoformat(
                    voro_user_fields["last_login"],
                )
                last_login = last_login.replace(tzinfo=datetime.UTC)
                date_joined = datetime.datetime.fromisoformat(
                    voro_user_fields["date_joined"],
                )
                date_joined = date_joined.replace(tzinfo=datetime.UTC)

                user_defaults = {
                    "is_superuser": voro_user_fields["is_superuser"],
                    "is_staff": voro_user_fields["is_staff"],
                    "is_active": voro_user_fields["is_active"],
                    "last_login": last_login,
                    "date_joined": date_joined,
                    "name": f"{voro_user_fields['first_name']} \
                            {voro_user_fields['last_name']}",
                }

                user, _ = User.objects.get_or_create(
                    email=email,
                    defaults=user_defaults,
                )
                user.save()

                for voro_group_id in voro_user_fields["groups"]:
                    for institution_id in voro_group_to_institution.get(
                        voro_group_id,
                        [],
                    ):
                        voro_institution_code = voro_institutions[institution_id]
                        voro_institution_code = voro_institution_code.replace("/", "_")
                        if Repository.objects.filter(
                            code=voro_institution_code,
                        ).exists():
                            repository = Repository.objects.get(
                                code=voro_institution_code,
                            )
                            userrole, _ = UserRole.objects.get_or_create(
                                user=user,
                                repository=repository,
                                role="contributor",
                                key_contact=False,
                            )
                            userrole.save()
