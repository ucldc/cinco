import boto3
import os


s3_bucket = os.environ.get("S3_BUCKET")
sns_topic_arn = os.environ.get("SNS_TOPIC_ARN")
textract_sns_role_arn = os.environ.get("TEXTRACT_SNS_ROLE")


def lambda_handler(event: dict[str, list[dict]], _):
    """
    This lambda function is triggered by an s3 event, whenever an object
    is created in the `S3_BUCKET` with the `supplemental-samples/`
    prefix. s3 event type is demonstrated here:
    https://docs.aws.amazon.com/lambda/latest/dg/with-s3-example.html#with-s3-example-test-dummy-event
    """
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        etag = record["s3"]["object"]["eTag"]
        start_textract_job(bucket, key, etag)


def start_textract_job(bucket: str, key: str, etag: str) -> tuple[str, str]:
    """
    start the textract job for specified s3 object, use the object's
    etag as the client request token - this prevents duplicate textract
    jobs from being started for the same object.
    """
    # start the textract job
    client = boto3.client("textract")
    response = client.start_document_text_detection(
        ClientRequestToken=etag,
        DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}},
        JobTag="supplemental-file",
        NotificationChannel={
            "SNSTopicArn": sns_topic_arn,
            "RoleArn": textract_sns_role_arn,
        },
        OutputConfig={"S3Bucket": s3_bucket, "S3Prefix": "textract-output"},
    )

    print(
        f"processing s3://{bucket}/{key} in textract job "
        f"{response['JobId']}; find results in s3://{s3_bucket}/"
        f"textract-output/{response['JobId']}"
    )
    return key, f"textract-output/{response['JobId']}"
