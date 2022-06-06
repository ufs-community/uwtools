import os
import boto3
from botocore.exceptions import ClientError as BotoError
from .s3 import S3


class S3S3(S3):

    @classmethod
    def copy(cls, source, target, progress=None):
        source_bucket, source_path = cls.extract_bucket(source)
        target_bucket, target_path = cls.extract_bucket(target)

        s3 = boto3.resource('s3')
        copy_source = dict(
            Bucket=source_bucket,
            Key=source_path
        )
        bucket = s3.Bucket(target_bucket)
        if progress:
            target_path = progress(source_path, target_path)
        try:
            bucket.copy(copy_source, target_path)
        except BotoError as e:
            if e.response['Error']['Code'] == 'InvalidObjectState':
                if e.response['Error']['StorageClass'] == 'GLACIER':
                    print(f'\nERROR: the file s3://{source} has been moved to GLACIER,\nplease restore it first.')
                    print()
                    exit()
                else:
                    raise FileNotFoundError(e)

    @classmethod
    def copy_transform(cls, source, target, transform, load_all, *args, **kwargs):
        """ Can be implemented later """
        raise ValueError('copy_transform from S3 to S3 is not supported')

    @classmethod
    def copy_tree(cls, source, target, progress=None):
        bucket, folder = cls.bucket_folder(source)
        for folder, path, file in cls.tree('s3://' + os.path.join(bucket, folder)):
            folder = folder.replace('s3://', '')
            source_path = os.path.join(folder, path, file)
            target_path = os.path.join(target, path, file)
            cls.copy(source_path, target_path, progress)
