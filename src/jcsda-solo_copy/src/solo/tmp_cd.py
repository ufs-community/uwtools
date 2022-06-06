import os


class TmpCD:
    """
        Changes the working directory, on exit, restores the previous one
        Meant to be used as:
        with TmpCD('/var/tmp'):
            # use tmp_dir
    """

    def __init__(self, tmp_path):
        self._tmp_path = tmp_path
        self._previous = os.getcwd()

    def __enter__(self):
        os.chdir(self._tmp_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self._previous)
