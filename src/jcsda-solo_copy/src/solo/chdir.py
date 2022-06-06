import os


class ChDir:
    """
        Changes the working directory to in a given directory.
        Meant to be used as:
        with ChDir('/var/tmp'):
            # work
        When exiting, the working directory is restored to its initial value.
    """

    def __init__(self, path):
        self._path = path
        self._previous = os.getcwd()

    def __enter__(self):
        self._previous = os.getcwd()
        os.chdir(self._path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self._previous)
