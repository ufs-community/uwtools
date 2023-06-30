# pylint: disable=missing-function-docstring


from uwtools.files import model


def test_imports():
    # Test that the expected modules have been imported into this package:
    for member in (
        "File",
        "Prefixes",
        "S3",
        "Unix",
    ):
        assert hasattr(model, member)
