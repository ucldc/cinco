import json
import os
from collections.abc import Iterator

import boto3
from django.conf import settings

from cincoctrl.findingaids.models import SupplementaryFile

s3_prefix = "textract-output"
sqs_url = os.environ.get("SQS_URL")

# SQS message structure:
#   MessageId: str, ReceiptHandle: str, MD5OfBody: str
#   Body: dict (SNS message)

# SNS message structure:
#   Type: str, MessageId: str, TopicArn: str, Timestamp: str,
#   SignatureVersion: str, Signature: str, SigningCertURL: str,
#   UnsubscribeURL: str
#   Message: dict (textract message)


def get_queued_messages() -> Iterator[dict]:
    """
    Poll the SQS queue for any messages.
    """
    sqs = boto3.client("sqs")
    response = sqs.receive_message(
        QueueUrl=sqs_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20,  # Enable long polling
    )
    sqs_messages = response.get("Messages", [])
    for sqs_message in sqs_messages:
        sns_message = json.loads(sqs_message.pop("Body"))
        textract_message = json.loads(sns_message.pop("Message"))

        read_message(textract_message)
        sqs.delete_message(QueueUrl=sqs_url, ReceiptHandle=sqs_message["ReceiptHandle"])


def read_message(textract_message: dict) -> None:
    """
    Read the textract message off the SQS queue, find the SupplementaryFile
    with the same pdf_file location, & update the status and textract_output
    attributes of the corresponding SupplementaryFile object.

    textract_message structure:
        JobId: str, Status: str, API: str, JobTag: str, Timestamp: int,
        DocumentLocation: dict[S3ObjectName: str, S3Bucket: str]
    """

    s3_obj = textract_message.get("DocumentLocation")
    pdf_file = f"s3://{s3_obj['S3Bucket']}/{s3_obj['S3ObjectName']}"

    supplementary_files = SupplementaryFile.objects.filter(pdf_file=pdf_file)
    if len(supplementary_files) == 1:
        supplementary_file = supplementary_files[0]
    else:
        error = f"Supplementary file not found for {pdf_file}"
        raise ValueError(error)

    status = textract_message.get("Status")
    job_id = textract_message.get("JobId")
    textract_output = f"s3://{settings.AWS_STORAGE_BUCKET_NAME}/{s3_prefix}/{job_id}"

    supplementary_file.status = status
    supplementary_file.textract_output = textract_output
    supplementary_file.save()

    # find ead with specified supplemental file
    # if all supplemental files for ead have status == SUCCEEDED,
    # re-index ead?
