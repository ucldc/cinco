import json

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from cincoctrl.findingaids.models import SupplementaryFile

s3_prefix = "textract-output"
sqs_url = settings.SQS_URL


class Command(BaseCommand):
    help = "Poll the SQS queue for any messages."

    def handle(self, *args, **kwargs):
        sqs = boto3.client("sqs")
        response = sqs.receive_message(
            QueueUrl=sqs_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,  # Enable long polling
        )
        sqs_messages = response.get("Messages", [])
        # SQS message structure: MessageId, ReceiptHandle, MD5OfBody,
        #   Body (dict, SNS message)

        self.stdout.write(f"Found {len(sqs_messages)} messages in SQS queue.")

        for sqs_message in sqs_messages:
            sns_message = json.loads(sqs_message.pop("Body"))
            # SNS message structure: Type, MessageId, TopicArn, Timestamp,
            #   SignatureVersion, Signature, SigningCertURL, UnsubscribeURL,
            #   Message (dict, textract message)

            # if sns_message['TopicArn'] is AmazonTextract topic
            self.stdout.write(f"SNS topic is: {sns_message['TopicArn']}")

            textract_message = json.loads(sns_message.pop("Message"))
            self.read_textract_message(textract_message)
            # endif

            self.stdout.write(
                f"Successfully read message {sqs_message['MessageId']} from SQS queue.",
            )

            sqs.delete_message(
                QueueUrl=sqs_url,
                ReceiptHandle=sqs_message["ReceiptHandle"],
            )

    def read_textract_message(self, textract_message: dict) -> None:
        """
        Read the textract message off the SQS queue, find the SupplementaryFile
        with the same pdf_file location, & update the status and textract_output
        attributes of the corresponding SupplementaryFile object.

        textract_message structure:
            JobId: str, Status: str, API: str, JobTag: str, Timestamp: int,
            DocumentLocation: dict[S3ObjectName: str, S3Bucket: str]
        """

        s3_obj = textract_message.get("DocumentLocation")
        s3_url = (
            f"https://{s3_obj['S3Bucket']}.s3.amazonaws.com/{s3_obj['S3ObjectName']}"
        )
        pdf_file_name = s3_url.removeprefix(settings.MEDIA_URL)
        supplementary_files = SupplementaryFile.objects.filter(pdf_file=pdf_file_name)

        if len(supplementary_files) == 1:
            supplementary_file = supplementary_files[0]
        else:
            error = f"Supplementary file not found for {pdf_file_name} at {s3_url}"
            raise CommandError(error)

        status = textract_message.get("Status")
        job_id = textract_message.get("JobId")
        textract_output = (
            f"s3://{settings.AWS_STORAGE_BUCKET_NAME}/{s3_prefix}/{job_id}"
        )

        supplementary_file.textract_status = status
        supplementary_file.textract_output = textract_output
        supplementary_file.save()

        # find ead with specified supplemental file
        # if all supplemental files for ead have status == SUCCEEDED,
        # re-index ead?
