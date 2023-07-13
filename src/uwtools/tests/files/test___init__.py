# pylint: disable=missing-function-docstring


from uwtools import files


def test_imports():
    # Test that the expected modules have been imported into this package:
    for member in (
        "File",
        "FileManager",
        "Prefixes",
        "S3",
        "S3FileManager",
        "Unix",
        "UnixFileManager",
    ):
        assert hasattr(files, member)
