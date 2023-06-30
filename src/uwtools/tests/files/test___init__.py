# pylint: disable=missing-function-docstring


from uwtools import files


def test_imports():
    # Test that the expected modules have been imported into this package:
    for member in (
        "FileManager",
        "S3FileManager",
        "UnixFileManager",
        "S3",
        "File",
        "Prefixes",
        "Unix",
    ):
        assert hasattr(files, member)
