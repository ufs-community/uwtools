# pylint: disable=missing-function-docstring

import shutil
from unittest.mock import patch

from uwtools.files import FileManager, S3FileManager, UnixFileManager
from uwtools.files.gateway import s3
from uwtools.files.model import S3, Prefixes, Unix
from uwtools.tests.support import fixture_uri


def test_FileManager_constructor_S3():
    assert isinstance(FileManager.get_file_manager(Prefixes.S3), S3FileManager)


def test_FileManager_constructor_Unix():
    assert isinstance(FileManager.get_file_manager(Prefixes.UNIX), UnixFileManager)


@patch.object(s3, "upload_file", return_value=None)
def test_S3_FileManager(upload_file):
    source = Unix(fixture_uri("files/a.txt"))
    destination = S3("s3://tests/fixtures/files/b.txt")
    fm: S3FileManager = FileManager.get_file_manager(Prefixes.S3)
    fm.copy([source], [destination])
    assert upload_file.copy.called_once_with([source], [destination])


@patch.object(shutil, "copy", return_value=None)
def test_Unix_FileManager(copy):
    source = Unix(fixture_uri("files/a.txt"))
    destination = Unix(fixture_uri("files/b.txt"))
    fm: UnixFileManager = FileManager.get_file_manager(Prefixes.UNIX)
    fm.copy([source], [destination.path])
    assert copy.copy.called_once_with([source], [destination])


def test_Unix_FileManager_Threaded(tmp_path):
    source = Unix(fixture_uri("files"))
    destination = Unix(tmp_path.as_uri())
    fm: UnixFileManager = FileManager.get_file_manager(Prefixes.UNIX)
    fm.copy([source], [destination.path])
    assert len(list(tmp_path.glob("*.txt"))) == 3
