import pytest


@pytest.fixture
def read_file():
    """
    Fixture to read a file that was written by a test and return contents
    Returns
    -------
    list of lines contains in the file
    """
    def _read(filename):
        try:
            with open(filename, 'r') as fh:
                fileout = fh.readlines()
        except Exception as e:
            raise AssertionError(f"failed reading {filename} as {e}")
        return fileout

    return _read