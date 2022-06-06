import os
from botocore.exceptions import ClientError
from .s3 import S3


class S3File(S3):

    def copy(self, source, target, create_target_path=True, progress=None):
        bucket, path = self.extract_bucket(source)
        if progress:
            target = progress(os.path.join(bucket, path), target)
        if create_target_path:
            target_path = os.path.dirname(target)
            if len(target_path):
                os.makedirs(target_path, exist_ok=True)
        with open(target, 'wb') as f:
            try:
                self._s3_client.download_fileobj(bucket, path, f)
            except ClientError as e:
                # clean up
                os.unlink(target)
                raise FileNotFoundError(e)

    @classmethod
    def copy_transform(cls, source, target, transform, load_all, *args, **kwargs):
        """ Can be implemented later """
        raise ValueError('copy_transform from S3 to File is not supported')

    def copy_tree(self, source, target, progress=None):
        bucket, folder = self.bucket_folder(source)
        for folder, path, file in self.tree('s3://' + os.path.join(bucket, folder)):
            source_path = os.path.join(bucket, folder, path, file)
            target_path = os.path.join(target, path, file)
            self.copy(source_path, target_path, progress)

