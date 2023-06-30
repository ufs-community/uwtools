# pylint: disable=missing-function-docstring


from uwtools.files import interface


def test_imports():
    # Test that the expected modules have been imported into this package:
    for member in (
        "FileManager",
        "S3FileManager",
        "UnixFileManager",
    ):
        assert hasattr(interface, member)
