# pylint: disable=missing-function-docstring,redefined-outer-name

from unittest.mock import patch

from pytest import fixture

from uwtools.api import file


@fixture
def args():
    return {
        "target_dir": "/target/dir",
        "config_file": "/config/file",
        "keys": ["a", "b"],
        "dry_run": True,
    }


def test_copy(args):
    with patch.object(file, "_FileCopier") as FileCopier:
        file.copy(**args)
    FileCopier.assert_called_once_with(**args)
    FileCopier().go.assert_called_once_with()


def test_link(args):
    with patch.object(file, "_FileLinker") as FileLinker:
        file.link(**args)
    FileLinker.assert_called_once_with(**args)
    FileLinker().go.assert_called_once_with()
