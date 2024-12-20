# given an s3 bucket and s3 key, start a textract job
# and return the job id
import os
import boto3

bucket = os.envrion.get("S3_BUCKET")


def start_textract_job(s3_bucket, s3_key):
    # start the textract job
    client = boto3.client("textract")
    response = client.start_document_text_detection(
        DocumentLocation={"S3Object": {"Bucket": s3_bucket, "Name": s3_key}},
        # idempotent string used to prevent duplicate jobs
        # ClientRequestToken='string',
        # identifier used in the completion notice sent to SNS
        # JobTag='string',
        # notification channel to send job completion status
        # NotificationChannel={
        #     'SNSTopicArn': 'string',
        #     'RoleArn': 'string'
        # }
        # sets if the output goes to a user-defined bucket
        OutputConfig={"S3Bucket": bucket, "S3Prefix": "textract-output"},
        # encryption on the results
        # KMSKeyId='string'
    )
    return response["JobId"]


def parse_results(blocks: list[dict]):
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


def read_textract_output(job_id: str):
    # get the textract job

    client = boto3.client("textract")
    response = client.get_document_text_detection(JobId=job_id)
    status = response["JobStatus"]

    if status != "SUCCEEDED":
        print(f"Job status: {status}")
        return response

    pages = response.get("DocumentMetadata", {}).get("Pages")
    model = response.get("DetectDocumentTextModelVersion")
    print(f"{pages} pages processed with {model} textract model version")
    print(f"Warnings: {response.get('Warnings')}")

    page = 1
    next_token = True
    while next_token:
        status_msg = response.get("StatusMessage")
        print(f"Page {page} {status}{f': {status_msg}' if status_msg else ''}")
        if status != "SUCCEEDED":
            print(status)
            return response

        yield parse_results(response.get("Blocks"))

        next_token = response.get("NextToken", False)

        if next_token:
            page += 1
            response = client.get_document_text_detection(
                JobId=job_id, NextToken=next_token
            )
        else:
            break
