# pylint: disable=missing-function-docstring

import os
from pathlib import Path
from unittest.mock import patch

import yaml
from pytest import mark, raises

from uwtools.api import config
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError, UWError
from uwtools.utils.file import FORMAT


def test_compare():
    kwargs: dict = {
        "config_1_path": "path1",
        "config_1_format": "fmt1",
        "config_2_path": "path2",
        "config_2_format": "fmt2",
    }
    with patch.object(config, "_compare") as _compare:
        config.compare(**kwargs)
    _compare.assert_called_once_with(
        **{
            **kwargs,
            "config_1_path": Path(kwargs["config_1_path"]),
            "config_2_path": Path(kwargs["config_2_path"]),
        }
    )


@mark.parametrize(
    "classname,f",
    [
        ("FieldTableConfig", config.get_fieldtable_config),
        ("INIConfig", config.get_ini_config),
        ("NMLConfig", config.get_nml_config),
        ("SHConfig", config.get_sh_config),
        ("YAMLConfig", config.get_yaml_config),
    ],
)
def test_get_config(classname, f):
    kwargs: dict = dict(config={})
    with patch.object(config, classname) as constructor:
        f(**kwargs)
    constructor.assert_called_once_with(**kwargs)


def test_realize():
    kwargs: dict = {
        "input_config": "path1",
        "input_format": "fmt1",
        "update_config": "path2",
        "update_format": "fmt2",
        "output_file": "path3",
        "output_format": "fmt3",
        "key_path": None,
        "values_needed": True,
        "total": True,
        "dry_run": False,
    }
    with patch.object(config, "_realize") as _realize:
        config.realize(**kwargs)
    _realize.assert_called_once_with(
        **{
            **kwargs,
            "input_config": Path(kwargs["input_config"]),
            "update_config": Path(kwargs["update_config"]),
            "output_file": Path(kwargs["output_file"]),
        }
    )


def test_realize_to_dict():
    kwargs: dict = {
        "input_config": "path1",
        "input_format": "fmt1",
        "update_config": None,
        "update_format": None,
        "key_path": None,
        "values_needed": True,
        "total": False,
        "dry_run": False,
        "stdin_ok": False,
    }
    with patch.object(config, "realize") as realize:
        config.realize_to_dict(**kwargs)
    realize.assert_called_once_with(
        **dict({**kwargs, **{"output_file": Path(os.devnull), "output_format": FORMAT.yaml}})
    )


def test_realize_update_config_from_stdin():
    with raises(UWError) as e:
        config.realize(input_config={}, output_file="output.yaml", update_format="yaml")
    assert str(e.value) == "Set stdin_ok=True to permit read from stdin"


def test_realize_update_config_none():
    input_config = {"n": 42}
    output_file = Path("output.yaml")
    with patch.object(config, "_realize") as _realize:
        config.realize(input_config=input_config, output_file=output_file)
    _realize.assert_called_once_with(
        input_config=input_config,
        input_format=None,
        update_config=None,
        update_format=None,
        output_file=output_file,
        output_format=None,
        key_path=None,
        values_needed=False,
        total=False,
        dry_run=False,
    )


@mark.parametrize("cfg", [{"foo": "bar"}, YAMLConfig(config={})])
def test_validate(cfg):
    kwargs: dict = {"schema_file": "schema-file", "config": cfg}
    with patch.object(config, "_validate_external") as _validate_external:
        assert config.validate(**kwargs) is True
        _validate_external.side_effect = UWConfigError()
        assert config.validate(**kwargs) is False
    _validate_external.assert_called_with(
        schema_file=Path(kwargs["schema_file"]),
        desc="config",
        config=kwargs["config"],
    )


@mark.parametrize("cast", (str, Path))
def test_validate_config_file(cast, tmp_path):
    cfg = tmp_path / "config.yaml"
    with open(cfg, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    kwargs: dict = {"schema_file": "schema-file", "config": cast(cfg)}
    with patch.object(config, "_validate_external", return_value=True) as _validate_external:
        assert config.validate(**kwargs)
    _validate_external.assert_called_once_with(
        schema_file=Path(kwargs["schema_file"]), desc="config", config=cfg
    )
