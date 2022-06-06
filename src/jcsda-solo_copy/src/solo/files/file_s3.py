import os
from .s3 import S3
from ..basic_files import tree


class FileS3(S3):

    def copy(self, source, target, progress=None):
        bucket, path = self.extract_bucket(target)
        if progress:
            path = progress(source, os.path.join(bucket, path))
        self._s3_client.upload_file(source, bucket, path)

    @classmethod
    def copy_transform(cls, source, target, transform, load_all, *args, **kwargs):
        """ Can be implemented later """
        raise ValueError('copy_transform from File to S3 is not supported')

    def copy_tree(self, source, target, progress=None):
        for source, path, file in tree(source):
            source_path = os.path.join(source, path, file)
            target_path = os.path.join(target, path, file)
            self.copy(source_path, target_path, progress)
