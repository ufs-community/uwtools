import os
from pathlib import Path
import boto3
from botocore.exceptions import ClientError


class S3:

    def __init__(self):
        self._s3_client = boto3.client('s3')

    def file_exists(self, path):
        p = Path(path)
        try:
            # head_object only returns metadata if the file exists.
            # Saves on volume transfer
            self._s3_client.head_object(Bucket=p.parts[0], Key='/'.join(p.parts[1:]))
        except ClientError:
            return False
        else:
            return True

    @classmethod
    def tree(cls, path):
        """
            Explores a path in a bucket and returns all the files names. Returns
            three components, full path, path and filename.
        """
        bucket, folder = cls.bucket_folder(path)
        if len(folder) and folder[-1] == '/':
            folder = folder[:-1]
        full = 's3://' + os.path.join(bucket, folder)
        s3 = boto3.client('s3')
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=folder)
        for page in pages:
            for obj in page['Contents']:
                name = obj['Key']
                path = os.path.dirname(name).replace(folder, '')
                if len(path) and path[0] == '/':
                    path = path[1:]
                yield full, path, os.path.basename(name)

    @classmethod
    def dir(cls, path):
        for full, directory, filename in cls.tree(path):
            yield filename, os.path.join(full, filename), directory == ''

    @staticmethod
    def makedirs(path, exist_ok=False):
        """ nothing to do in S3"""
        pass

    @staticmethod
    def symlink(source, target):
        """ nothing to do in S3"""
        pass

    @staticmethod
    def extract_bucket(s3_path):
        path = s3_path.split('/')
        return path[0], '/'.join(path[1:])

    @staticmethod
    def bucket_folder(path):
        path = path.replace('s3://', '')
        parts = path.split('/')
        return parts[0], '/'.join(parts[1:])
