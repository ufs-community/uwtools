import os
from .basic import unique_id


class TmpFile:
    """
        Create a temporary filename in a given directory. Filenames generated are unique
        Meant to be used as:
        with TmpFile('/var/tmp', delete=True) as tmp:
            with open(tmp.path(), 'w') as f:
                # f.write something
        if delete is True (default), delete on exit.
        if the temporary dir given does not exist, it is created.
    """

    def __init__(self, tmp_path, delete=True):
        self._tmp_path = tmp_path
        self._filename = unique_id()
        self._delete = delete
        os.makedirs(tmp_path, exist_ok=True)

    def path(self):
        return os.path.join(self._tmp_path, self._filename)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._delete:
            os.unlink(self.path())
