# pylint: disable=missing-function-docstring,protected-access

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from uwtools.api import config
from uwtools.config.formats.yaml import YAMLConfig


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


@pytest.mark.parametrize(
    "classname,f",
    [
        ("_FieldTableConfig", config.get_fieldtable_config),
        ("_INIConfig", config.get_ini_config),
        ("_NMLConfig", config.get_nml_config),
        ("_SHConfig", config.get_sh_config),
        ("_YAMLConfig", config.get_yaml_config),
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
        "output_block": None,
        "output_file": "path2",
        "output_format": "fmt2",
        "supplemental_configs": ["path3"],
        "values_needed": True,
        "total": True,
        "dry_run": True,
    }
    with patch.object(config, "_realize") as _realize:
        config.realize(**kwargs)
    _realize.assert_called_once_with(
        **{
            **kwargs,
            "input_config": Path(kwargs["input_config"]),
            "output_file": Path(kwargs["output_file"]),
            "supplemental_configs": [Path(x) for x in kwargs["supplemental_configs"]],
        }
    )


def test_realize_to_dict():
    kwargs: dict = {
        "input_config": "path1",
        "input_format": "fmt1",
        "supplemental_configs": ["path3"],
        "values_needed": True,
        "dry_run": True,
        "stdin_ok": False,
    }
    with patch.object(config, "_realize") as _realize:
        config.realize_to_dict(**kwargs)
    _realize.assert_called_once_with(
        **dict({**kwargs, **{"output_file": Path(os.devnull), "output_format": None}})
    )


@pytest.mark.parametrize("cfg", [{"foo": "bar"}, YAMLConfig(config={})])
def test_validate(cfg):
    kwargs: dict = {"schema_file": "schema-file", "config": cfg}
    with patch.object(config, "_validate_yaml", return_value=True) as _validate_yaml:
        assert config.validate(**kwargs)
    _validate_yaml.assert_called_once_with(
        schema_file=Path(kwargs["schema_file"]), config=kwargs["config"]
    )


def test_validate_config_file(tmp_path):
    cfg = tmp_path / "config.yaml"
    with open(cfg, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    kwargs: dict = {"schema_file": "schema-file", "config": cfg}
    with patch.object(config, "_validate_yaml", return_value=True) as _validate_yaml:
        assert config.validate(**kwargs)
    _validate_yaml.assert_called_once_with(schema_file=Path(kwargs["schema_file"]), config=cfg)
