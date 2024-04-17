# pylint: disable=missing-function-docstring,redefined-outer-name

from pathlib import Path
from unittest.mock import patch

from pytest import fixture

from uwtools.api import file


@fixture
def kwargs():
    return {
        "target_dir": "/target/dir",
        "config": "/config/file",
        "keys": ["a", "b"],
        "dry_run": True,
    }


def test_copy(kwargs):
    with patch.object(file, "_FileCopier") as FileCopier:
        file.copy(**kwargs)
    FileCopier.assert_called_once_with(
        **{**kwargs, "target_dir": Path(kwargs["target_dir"]), "config": Path(kwargs["config"])}
    )
    FileCopier().go.assert_called_once_with()


def test_link(kwargs):
    with patch.object(file, "_FileLinker") as FileLinker:
        file.link(**kwargs)
    FileLinker.assert_called_once_with(
        **{**kwargs, "target_dir": Path(kwargs["target_dir"]), "config": Path(kwargs["config"])}
    )
    FileLinker().go.assert_called_once_with()
