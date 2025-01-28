import json
import logging
from collections.abc import Iterator

import boto3

logger = logging.getLogger(__name__)


def _get_text(blocks: list[dict]) -> str:
    # blocks has keys: [BlockType: str, Confidence: float, Text: str,
    # TextType: str, RowIndex: int, ColumnIndex: int, RowSpan: int,
    # ColumnSpan: int, Geometry: dict, Id: str,
    # Relationships: list[dict], EntityTypes: list[str],
    # SelectionStatus: str, Page: int, Query: dict]

    # warnings has keys: [ErrorCode: str, Pages: list[int]]
    full_text = ""
    for block in blocks:
        if block["BlockType"] == "LINE":
            if block.get("Text"):
                full_text += block["Text"] + " "

    return full_text


def _read_textract_s3_output(bucket: str, key: str) -> Iterator[dict]:
    client = boto3.client("s3")
    response = client.list_objects_v2(Bucket=bucket, Prefix=key)
    s3_pages = response.get("Contents", [])

    for s3_page in s3_pages:
        textract_response = client.get_object(Bucket=bucket, Key=s3_page.get("Key"))
        yield json.loads(textract_response.get("Body").read())


def read_textract_job(s3_bucket, s3_key):
    pages_text = []

    for textract_response_page in _read_textract_s3_output(s3_bucket, s3_key):
        status = textract_response_page["JobStatus"]
        status_msg = textract_response_page.get("StatusMessage")
        warnings = textract_response_page.get("Warnings")
        debug_msg = (
            f"Textract {status}{f': {status_msg}' if status_msg else ''}"
            f"{f' with warnings: {warnings}' if warnings else ''}"
        )
        logger.debug(debug_msg)

        if status != "SUCCEEDED":
            error_msg = f"Textract job failed with status {status}"
            raise ValueError(error_msg)

        pages = textract_response_page.get("DocumentMetadata", {}).get("Pages")
        version = textract_response_page.get("DetectDocumentTextModelVersion")
        debug_msg = f"{pages} pages processed with textract model {version}"
        logger.debug(debug_msg)

        blocks = textract_response_page.get("Blocks")
        pages_text.append(_get_text(blocks))

    document = {"full_text": " ".join(pages_text)}
    return document  # noqa: RET504


# def _read_textract_direct_output(job_id: str) -> Iterator[dict]:
#     # get the textract job
#     client = boto3.client("textract")
#     request = {"JobId": job_id}

#     next_token = True
#     while next_token:
#         textract_response = client.get_document_text_detection(**request)
#         next_token = textract_response.get("NextToken", False)
#         yield textract_response
#         request = request.update({"NextToken": next_token})


# def start_textract_job(s3_bucket, s3_key, output_bucket):
#     # start the textract job
#     client = boto3.client("textract")
#     response = client.start_document_text_detection(
#         DocumentLocation={"S3Object": {"Bucket": s3_bucket, "Name": s3_key}},
#         # idempotent string used to prevent duplicate jobs
#         # ClientRequestToken='string',
#         # identifier used in the completion notice sent to SNS
#         # JobTag='string',
#         # notification channel to send job completion status
#         # NotificationChannel={
#         #     'SNSTopicArn': 'string',
#         #     'RoleArn': 'string'
#         # }
#         # sets if the output goes to a user-defined bucket
#         OutputConfig={"S3Bucket": output_bucket, "S3Prefix": "textract-output"},
#         # encryption on the results
#         # KMSKeyId='string'
#     )
#     return response["JobId"]
