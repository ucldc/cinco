import os
import boto3
import json
from typing import Iterator

from cincoctrl.findingaids.models import SupplementaryFile


s3_bucket = os.environ.get("S3_BUCKET")
sqs_url = os.environ.get("SQS_ARN")


def get_queued_messages() -> Iterator[dict]:
    # poll the sqs queue
    sqs = boto3.client("sqs")
    response = sqs.receive_message(
        QueueUrl=sqs_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20,  # Enable long polling
    )
    sqs_messages = response.get("Messages", [])
    for sqs_message in sqs_messages:
        yield sqs_message

        sqs.delete_message(QueueUrl=sqs_url, ReceiptHandle=sqs_message["ReceiptHandle"])


def read_messages():
    """
    sqs messages has keys:
        MessageId: str, ReceiptHandle: str, MD5OfBody: str, Body: dict
    Body, here, is the sns_message, which has keys:
        Type: str, MessageId: str, TopicArn: str, Message: dict,
        Timestamp: str, SignatureVersion: str, Signature: str,
        SigningCertURL: str, UnsubscribeURL: str
    Message, here, is the textract_message, which has keys:
        JobId: str, Status: str, API: str, JobTag: str, Timestamp: int,
        DocumentLocation: dict[S3ObjectName: str, S3Bucket: str]
    """
    for sqs_message in get_queued_messages():
        sns_message = json.loads(sqs_message.pop("Body"))
        textract_message = json.loads(sns_message.pop("Message"))

        s3_obj = textract_message.get("DocumentLocation")
        pdf_file = f"s3://{s3_obj['S3Bucket']}/{s3_obj['S3ObjectName']}"

        supplementary_files = SupplementaryFile.objects.filter(pdf_file=pdf_file)
        if len(supplementary_files) == 1:
            supplementary_file = supplementary_files[0]
        else:
            raise ValueError(f"Supplementary file not found for {pdf_file}")

        status = textract_message.get("Status")
        job_id = textract_message.get("JobId")
        textract_output = f"s3://{s3_bucket}/textract-output/{job_id}"

        supplementary_file.status = status
        supplementary_file.textract_output = textract_output
        supplementary_file.save()

        # find ead with specified supplemental file
        # if all supplemental files for ead have status == SUCCEEDED,
        # re-index ead?
