import boto3
import json

from typing import Iterator


def parse_textract_blocks(blocks: list[dict]) -> str:
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


def read_textract(s3_bucket, s3_key):
    full_text = []

    for textract_response in read_textract_s3_output(s3_bucket, s3_key):
        status = textract_response["JobStatus"]
        status_msg = textract_response.get("StatusMessage")
        warnings = textract_response.get("Warnings")
        print(
            f"Textract {status}{f': {status_msg}' if status_msg else ''}"
            f"{f' with warnings: {warnings}' if warnings else ''}"
        )

        if status != "SUCCEEDED":
            raise ValueError(f"Textract job failed with status {status}")

        pages = textract_response.get("DocumentMetadata", {}).get("Pages")
        version = textract_response.get("DetectDocumentTextModelVersion")
        print(f"{pages} pages processed with textract model {version}")

        blocks = textract_response.get("Blocks")
        full_text.append(parse_textract_blocks(blocks))

    return full_text


def read_textract_s3_output(bucket: str, key: str) -> Iterator[dict]:
    client = boto3.client("s3")
    response = client.list_objects_v2(Bucket=bucket, Prefix=key)
    s3_pages = response.get("Contents", [])

    for s3_page in s3_pages:
        textract_response = client.get_object(Bucket=bucket, Key=s3_page.get("Key"))
        yield json.loads(textract_response.get("Body").read())


def read_textract_direct_output(job_id: str) -> Iterator[dict]:
    # get the textract job
    client = boto3.client("textract")
    request = {"JobId": job_id}

    next_token = True
    while next_token:
        textract_response = client.get_document_text_detection(**request)
        next_token = textract_response.get("NextToken", False)
        yield textract_response
        request = request.update({"NextToken": next_token})
