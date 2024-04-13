# pylint: disable=missing-function-docstring,redefined-outer-name

from pathlib import Path
from unittest.mock import patch

from pytest import fixture, raises

from uwtools.api import file
from uwtools.exceptions import UWError


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


def test_copy_stdin_not_ok(kwargs):
    kwargs["config"] = None
    with raises(UWError) as e:
        file.copy(**kwargs)
    assert str(e.value) == "Set stdin_ok=True to enable read from stdin"


def test_link(kwargs):
    with patch.object(file, "_FileLinker") as FileLinker:
        file.link(**kwargs)
    FileLinker.assert_called_once_with(
        **{**kwargs, "target_dir": Path(kwargs["target_dir"]), "config": Path(kwargs["config"])}
    )
    FileLinker().go.assert_called_once_with()


def test_link_stdin_not_ok(kwargs):
    kwargs["config"] = None
    with raises(UWError) as e:
        file.link(**kwargs)
    assert str(e.value) == "Set stdin_ok=True to enable read from stdin"
