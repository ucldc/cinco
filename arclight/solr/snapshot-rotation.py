import boto3


def main():
    s3_client = boto3.client("s3", endpoint_url="http://minio.cinco.orb.local:9000")

    bucket_name = "cinco-dev"
    snapshot_prefix = "solr_backups/snapshot."
    resp = s3_client.list_objects_v2(
        Bucket=bucket_name, Prefix=snapshot_prefix, Delimiter="/"
    )
    snapshots = [snapshot["Prefix"] for snapshot in resp.get("CommonPrefixes", [])]
    old_snapshots = snapshots[:-5]
    for snapshot in old_snapshots:
        resp = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=snapshot)
        s3_objects = [{"Key": c["Key"]} for c in resp.get("Contents", [])]
        s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": s3_objects})


if __name__ == "__main__":
    main()
