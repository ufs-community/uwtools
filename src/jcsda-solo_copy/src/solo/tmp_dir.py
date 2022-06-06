import os
import shutil
from .basic import unique_id


class TmpDir:
    """
        Create a temporary directory in a given directory. Directory names generated are unique
        Meant to be used as:
        with TmpDir('/var/tmp', delete=True) as tmp_dir:
            # use tmp_dir
        if delete is True (default), the directory and everything underneath is removed
        if the directory given does not exist, it is created.
    """

    def __init__(self, tmp_path, delete=True):
        self._tmp_path = os.path.join(tmp_path, unique_id())
        self._delete = delete
        os.makedirs(tmp_path, exist_ok=True)

    def path(self):
        return self._tmp_path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._delete:
            shutil.rmtree(self._tmp_path)
