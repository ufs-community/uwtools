# pylint: disable=missing-function-docstring,protected-access

import os
from unittest.mock import patch

import pytest
import yaml

from uwtools.api import config
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.utils.file import FORMAT


def test_compare():
    kwargs: dict = {
        "config_a_path": "path1",
        "config_a_format": "fmt1",
        "config_b_path": "path2",
        "config_b_format": "fmt2",
    }
    with patch.object(config, "_compare") as _compare:
        config.compare(**kwargs)
    _compare.assert_called_once_with(**kwargs)


def test_realize():
    kwargs: dict = {
        "input_config": "path1",
        "input_format": "fmt1",
        "output_file": "path2",
        "output_format": "fmt2",
        "values": "path3",
        "values_format": "fmt3",
        "values_needed": True,
        "dry_run": True,
    }
    with patch.object(config, "_realize") as _realize:
        config.realize(**kwargs)
    _realize.assert_called_once_with(**kwargs)


def test_realize_to_dict():
    kwargs: dict = {
        "input_config": "path1",
        "input_format": "fmt1",
        "values": "path3",
        "values_format": "fmt3",
        "values_needed": True,
        "dry_run": True,
    }
    with patch.object(config, "_realize") as _realize:
        config.realize_to_dict(**kwargs)
    _realize.assert_called_once_with(
        **dict({**kwargs, **{"output_file": os.devnull, "output_format": None}})
    )


@pytest.mark.parametrize(
    "infmt,outfmt,success_expected",
    [
        (FORMAT.atparse, FORMAT.jinja2, True),
        ("invalid", FORMAT.jinja2, False),
        (FORMAT.atparse, "invalid", False),
    ],
)
def test_translate(infmt, outfmt, success_expected):
    kwargs: dict = {
        "input_file": "path1",
        "input_format": infmt,
        "output_file": "path2",
        "output_format": outfmt,
        "dry_run": True,
    }
    with patch.object(config, "_convert_atparse_to_jinja2") as _catj:
        assert config.translate(**kwargs) is success_expected
    if success_expected:
        _catj.assert_called_once_with(
            input_file=kwargs["input_file"],
            output_file=kwargs["output_file"],
            dry_run=kwargs["dry_run"],
        )


@pytest.mark.parametrize("cfg", [{"foo": "bar"}, YAMLConfig(config={})])
def test_validate(cfg):
    kwargs: dict = {"schema_file": "schema-file", "config": cfg}
    with patch.object(config, "_validate_yaml", return_value=True) as _validate_yaml:
        assert config.validate(**kwargs)
    _validate_yaml.assert_called_once_with(
        schema_file=kwargs["schema_file"], config=kwargs["config"]
    )


def test_validate_config_file(tmp_path):
    cfg = tmp_path / "config.yaml"
    with open(cfg, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    kwargs: dict = {"schema_file": "schema-file", "config": cfg}
    with patch.object(config, "_validate_yaml", return_value=True) as _validate_yaml:
        assert config.validate(**kwargs)
    _validate_yaml.assert_called_once_with(
        schema_file=kwargs["schema_file"], config=YAMLConfig(cfg)
    )


def test__ensure_config_arg_type_config_obj():
    config_obj = YAMLConfig(config={})
    assert config._ensure_config_arg_type(config=config_obj) is config_obj


def test__ensure_config_arg_type_dict():
    config_dict = {"foo": 88}
    config_obj = config._ensure_config_arg_type(config=config_dict)
    assert isinstance(config_obj, YAMLConfig)
    assert config_obj.data == config_dict


def test__ensure_config_arg_type_path():
    config_path = "/path/to/config.yaml"
    config_obj = config._ensure_config_arg_type(config=config_path)
    assert isinstance(config_obj, str)
    assert config_obj is config_path
