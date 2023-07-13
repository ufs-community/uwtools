"""
Gateway for interacting with S3.
"""

import logging
import os
import pathlib
from typing import Optional

import boto3
from botocore.exceptions import ClientError

S3_CLIENT = boto3.client("s3")


def download_file(bucket_name: str, source_name: str, target_name: str) -> None:
    """
    Download files from S3.
    """
    S3_CLIENT.download_file(bucket_name, source_name, target_name)


def exists(_path: pathlib.Path) -> bool:
    """
    Returns True if file exists.
    """
    try:
        S3_CLIENT.head_object(Bucket=_path.parts[0], Key="/".join(_path.parts[1:]))
    except ClientError:
        return False
    return True


def upload_file(source_path: str, bucket: str, target_name: Optional[str] = None) -> bool:
    """
    Upload a file to an S3 bucket.
    """

    # If S3 object_name was not specified, use file name.

    if target_name is None:
        target_name = os.path.basename(source_path)

    # Upload the file.

    try:
        S3_CLIENT.upload_file(source_path, bucket, target_name)
    except ClientError as error:
        logging.error(error)
        return False
    return True
