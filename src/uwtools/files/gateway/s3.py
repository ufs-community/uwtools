## pylint: disable=unused-variable
"""
Gateway for interacting with S3
"""

import logging
import os
import pathlib

import boto3
from botocore.exceptions import ClientError

S3_CLIENT = boto3.client("s3")


def exists(_path: pathlib.Path):
    """returns True if file exists
    #TODO hacky for a common function
    """
    try:
        S3_CLIENT.head_object(Bucket=_path.parts[0], Key="/".join(_path.parts[1:]))
    except ClientError:
        return False
    return True


def upload_file(source_path, bucket, target_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if target_name is None:
        target_name = os.path.basename(source_path)

    # Upload the file
    try:
        S3_CLIENT.upload_file(source_path, bucket, target_name)
    except ClientError as error:
        logging.error(error)
        return False
    return True


def download_file(bucket_name, source_name, target_name):
    """download files from s3"""
    S3_CLIENT.download_file(bucket_name, source_name, target_name)
