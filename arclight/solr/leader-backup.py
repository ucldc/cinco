#!/usr/bin/env python3

"""
backup the leader to solr:
    manage snapshot rotation
    don't backup if the current index version matches the latest snapshot version
# "http://localhost:8983/solr/arclight/replication?command=backup&repository=s3&location=solr_backups"
# "http://localhost:8983/solr/arclight/replication?command=details"
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any

import boto3
import botocore
import requests

AWS = {
    "region_name": os.environ.get("AWS_REGION"),
    "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID"),
    "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
    "endpoint_url": os.environ.get("SOLR_S3_ENDPOINT"),
}
AWS = {k: v for k, v in AWS.items() if v is not None}

S3_BUCKET = os.environ.get("SOLR_S3_BUCKET")
SOLR_URL = os.environ.get("SOLR_URL", "http://localhost:8983/solr/arclight")

SNAPSHOT_PREFIX = "solr_backups/"
VERSION_FILE = f"{SNAPSHOT_PREFIX}index_version.txt"
SOLR_URL = os.environ.get("SOLR_URL", "http://localhost:8983/solr/arclight")


def log_msg(status: str, message: str, payload: Any) -> None:
    print(
        datetime.now().astimezone(),
        json.dumps(
            {
                "arclight_backup_status": status,
                "message": message,
                "context": payload,
            }
        ),
    )


if not S3_BUCKET:
    log_msg("failed", "SOLR_S3_BUCKET environment variable is not set", {})
    sys.exit(1)


def get_latest_snapshot_version() -> int | None:
    # fail & exit if we can't connect to s3; proceed if latest version not found
    s3 = boto3.client("s3", **AWS)
    try:
        latest_version = s3.get_object(
            Bucket=S3_BUCKET, Key=f"{SNAPSHOT_PREFIX}index_version.txt"
        )
        return int(latest_version["Body"].read().decode("utf-8").strip())
    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            return None
        log_msg(
            "failed",
            "s3 connection error",
            {
                "s3_error": f"{type(e).__name__}: {e}",
                "s3_request_context": {"bucket": S3_BUCKET, "key": VERSION_FILE, **AWS},
            },
        )
        sys.exit(1)
    except (KeyError, AttributeError, ValueError):
        return None


def get_latest_snapshot_name() -> str | None:
    s3 = boto3.client("s3", **AWS)
    try:
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET, Prefix=SNAPSHOT_PREFIX, Delimiter="/"
        )
        common_prefixes = [
            prefix["Prefix"] for prefix in response.get("CommonPrefixes", [])
        ]
        if common_prefixes:
            return common_prefixes[-1]  # return the latest snapshot prefix
        return None
    except botocore.exceptions.ClientError as e:
        log_msg(
            "failed",
            "s3 connection error",
            {
                "s3_error": f"{type(e).__name__}: {e}",
                "s3_request_context": {
                    "bucket": S3_BUCKET,
                    "prefix": SNAPSHOT_PREFIX,
                    **AWS,
                },
            },
        )
        sys.exit(1)


def get_current_index_version() -> int | None:
    solr_resp = solr_request("?command=details")
    if "details" not in solr_resp or "indexVersion" not in solr_resp["details"]:
        log_msg("failed", "malformed solr response", {"solr_resp": solr_resp})
        sys.exit(1)
    return solr_resp["details"]["indexVersion"]


def start_backup() -> dict[str, Any]:
    solr_resp = solr_request("?command=backup&repository=s3&location=solr_backups")
    respstatus = solr_resp.get("status")
    if respstatus != "OK":
        log_msg(
            "failed",
            "error issuing replication?command=backup",
            {"solr_resp": solr_resp},
        )
        sys.exit(1)

    return solr_resp


def poll_solr_for_backup_completion(
    last_snapshot_name, timeout_seconds: int = 60, polling_seconds: int = 5
) -> dict[str, Any]:
    start_time = time.time()
    while True:
        solr_resp = solr_request("?command=details")
        backupname = solr_resp.get("details", {}).get("backup", {}).get("directoryName")
        if backupname != last_snapshot_name:
            backupstatus = (
                solr_resp.get("details", {}).get("backup", {}).get("status", "").lower()
            )
            if backupstatus == "success":
                return solr_resp
            if backupstatus == "failed":
                log_msg(
                    "failed",
                    "Solr backup failed - see solr response for details",
                    {"solr_resp": solr_resp},
                )
                sys.exit(1)
        if time.time() - start_time >= timeout_seconds:
            log_msg(
                "unknown",
                "Backup did not complete within timeout",
                {"timeout": timeout_seconds, "solr_resp": solr_resp},
            )
            sys.exit(1)
        time.sleep(polling_seconds)


def rotate_snapshots():
    s3_client = boto3.client("s3", **AWS)

    snapshot_prefix = f"{SNAPSHOT_PREFIX}snapshot."
    snapshot = None
    s3_objects = None

    try:
        resp = s3_client.list_objects_v2(
            Bucket=S3_BUCKET, Prefix=snapshot_prefix, Delimiter="/"
        )
        snapshots = [snapshot["Prefix"] for snapshot in resp.get("CommonPrefixes", [])]
        old_snapshots = snapshots[:-5]
        for snapshot in old_snapshots:
            resp = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=snapshot)
            s3_objects = [{"Key": c["Key"]} for c in resp.get("Contents", [])]
            s3_client.delete_objects(Bucket=S3_BUCKET, Delete={"Objects": s3_objects})
    except botocore.exceptions.ClientError as e:
        log_msg(
            "error",
            "s3 snapshot rotation failed",
            {
                "s3_error": f"{type(e).__name__}: {e}",
                "snapshot_rotation_context": {
                    "prefix": snapshot_prefix,
                    "snapshot": snapshot,
                    "s3_objects": s3_objects,
                },
                "s3_request_context": {
                    "bucket": S3_BUCKET,
                    "prefix": snapshot_prefix,
                    **AWS,
                },
            },
        )


def solr_request(params: str) -> dict[str, Any]:
    url = f"{SOLR_URL}/replication{params}"
    response = requests.get(url, timeout=30)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        log_msg(
            "failed",
            "solr request error",
            {"request_url": url, "error": f"{type(e).__name__}: {e}"},
        )
        sys.exit(1)

    return response.json()


def parse_iso8601(value: str | None):
    if not value:
        return None
    value = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def main() -> None:
    latest_snapshot = get_latest_snapshot_version()
    last_snapshot_name = get_latest_snapshot_name()
    current_version = get_current_index_version()
    if latest_snapshot == current_version or not current_version:
        log_msg(
            "skipped",
            "latest snapshot version == current index version",
            {
                "latest_snapshot_version": latest_snapshot,
                "current_index_version": current_version,
            },
        )
        sys.exit(0)

    # Start backup
    start_backup()

    solr_backup_details = poll_solr_for_backup_completion(
        last_snapshot_name, timeout_seconds=60, polling_seconds=5
    )
    details = solr_backup_details.get("details", {})
    index_version = str(details.get("indexVersion"))
    backup = details.get("backup", {})
    backupname = backup.get("directoryName")
    start_dt = parse_iso8601((backup.get("startTime") or "").strip())
    end_dt = parse_iso8601((backup.get("endTime") or "").strip())
    elapsedtime = 0
    if start_dt and end_dt:
        elapsedtime = int((end_dt - start_dt).total_seconds())

    s3 = boto3.client("s3", **AWS)
    s3.put_object(
        Bucket=S3_BUCKET, Key=VERSION_FILE, Body=(index_version or "").encode("utf-8")
    )

    rotate_snapshots()

    log_msg(
        "success",
        f"Backup completed successfully in {elapsedtime}s at {backupname}",
        solr_backup_details,
    )


if __name__ == "__main__":
    main()
