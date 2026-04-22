from pathlib import Path
from unittest.mock import patch

from pytest import raises

from uwtools.api import ecflow
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWError


def test_api_ecflow_realize():
    path1, path2 = Path("foo"), Path("bar")
    with patch.object(ecflow, "_realize") as _realize:
        ecflow.realize(config=path1, output_path=path2)
    _realize.assert_called_once_with(config=path1, output_path=path2, scripts_path=None)


def test_api_ecflow_realize__with_scripts():
    path1, path2, path3 = Path("foo"), Path("bar"), Path("baz")
    with patch.object(ecflow, "_realize") as _realize:
        ecflow.realize(config=path1, output_path=path2, scripts_path=path3)
    _realize.assert_called_once_with(config=path1, output_path=path2, scripts_path=path3)


def test_api_ecflow_validate__path():
    path = Path("foo")
    with patch.object(ecflow, "_validate") as _validate:
        ecflow.validate(config=path)
    _validate.assert_called_once_with(config=path)


def test_api_ecflow_validate__str():
    with patch.object(ecflow, "_validate") as _validate:
        ecflow.validate(config="foo")
    _validate.assert_called_once_with(config=Path("foo"))


def test_api_ecflow_validate__dict():
    cfg: dict = {"ecflow": {}}
    with patch.object(ecflow, "_validate") as _validate:
        ecflow.validate(config=cfg)
    _validate.assert_called_once_with(config=cfg)


def test_api_ecflow_validate__yamlconfig():
    cfg = YAMLConfig({"ecflow": {}})
    with patch.object(ecflow, "_validate") as _validate:
        ecflow.validate(config=cfg)
    _validate.assert_called_once_with(config=cfg)


def test_api_ecflow_validate__stdin():
    with patch.object(ecflow, "_validate") as _validate:
        ecflow.validate(stdin_ok=True)
    _validate.assert_called_once_with(config=None)


def test_api_ecflow_validate__no_stdin_no_config():
    with raises(UWError) as e:
        ecflow.validate()
    assert "Set stdin_ok=True to permit read from stdin" in str(e.value)
