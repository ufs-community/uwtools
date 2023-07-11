# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.files.gateway.s3 module.
"""

from pathlib import Path
from unittest.mock import patch

from pytest import fixture

from uwtools.files.gateway import s3


@fixture
def exc():
    return s3.ClientError(operation_name="NA", error_response={})


@fixture
def upload_kwargs():
    return dict(source_path="/foo/bar", bucket="bucket")


def test_download_file():
    kwargs = dict(bucket_name="bucket", source_name="source", target_name="target")
    with patch.object(s3, "S3_CLIENT") as S3_CLIENT:
        s3.download_file(**kwargs)
        assert S3_CLIENT.download_file.called_once_with(*kwargs.values())


def test_exists_false(exc):
    with patch.object(s3, "S3_CLIENT") as S3_CLIENT:
        S3_CLIENT.head_object.side_effect = exc
        assert not s3.exists(Path("/foo/bar"))


def test_exists_true():
    with patch.object(s3, "S3_CLIENT") as S3_CLIENT:
        S3_CLIENT.head_object.return_value = True
        assert s3.exists(Path("/foo/bar"))


def test_upload_file_failure(exc, upload_kwargs):
    with patch.object(s3, "S3_CLIENT") as S3_CLIENT:
        S3_CLIENT.upload_file.side_effect = exc
        assert not s3.upload_file(**upload_kwargs)


def test_upload_file_success(upload_kwargs):
    with patch.object(s3, "S3_CLIENT") as S3_CLIENT:
        assert s3.upload_file(**upload_kwargs)
        S3_CLIENT.upload_file.assert_called_once_with(*upload_kwargs.values(), "bar")
