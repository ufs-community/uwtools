# pylint: disable=all
import shutil
from unittest.mock import patch

from uwtools.files import FileManager, S3FileManager, UnixFileManager
from uwtools.files.gateway import s3
from uwtools.files.model import S3, Prefixes, Unix


def test_FileManager():
    actual = FileManager.get_file_manager(Prefixes.S3)
    assert isinstance(actual, S3FileManager)
    actual = FileManager.get_file_manager(Prefixes.UNIX)
    print(actual.__class__.__name__)
    assert isinstance(actual, UnixFileManager)


@patch.object(s3, "upload_file", return_value=None)
def test_S3_FileManager(mock_file_manager):

    source = Unix("file://tests/fixtures/files/a.txt")
    destination = S3("s3://tests/fixtures/files/b.txt")

    fm: S3FileManager = FileManager.get_file_manager(Prefixes.S3)
    fm.copy([source], [destination])
    assert mock_file_manager.copy.called_once_with([source], [destination])


@patch.object(shutil, "copy", return_value=None)
def test_Unix_FileManager(mock_file_manager):

    source = Unix("file://tests/fixtures/files/a.txt")
    destination = Unix("file://tests/fixtures/files/b.txt")

    fm: UnixFileManager = FileManager.get_file_manager(Prefixes.UNIX)
    fm.copy([source], [destination])
    assert mock_file_manager.copy.called_once_with([source], [destination])
