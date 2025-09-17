import os
from pathlib import Path
from unittest.mock import patch

import yaml
from pytest import mark, raises

from uwtools.api import config
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError, UWError
from uwtools.utils.file import FORMAT


def test_api_config_compare():
    kwargs: dict = {
        "path1": "path1",
        "format1": "fmt1",
        "path2": "path2",
        "format2": "fmt2",
    }
    with patch.object(config, "_compare") as _compare:
        config.compare(**kwargs)
    _compare.assert_called_once_with(
        **{
            **kwargs,
            "path1": Path(kwargs["path1"]),
            "path2": Path(kwargs["path2"]),
        }
    )


@mark.parametrize("output_file", [None, "/path/to/out.yaml"])
@mark.parametrize("input_format", [None, FORMAT.yaml, FORMAT.nml])
@mark.parametrize("output_format", [None, FORMAT.yaml, FORMAT.nml])
def test_api_config_compose(output_file, input_format, output_format):
    pathstrs = ["/path/to/c1.yaml", "/path/to/c2.yaml"]
    kwargs: dict = {
        "configs": pathstrs,
        "realize": False,
        "output_file": output_file,
        "input_format": input_format,
        "output_format": output_format,
    }
    with patch.object(config, "_compose") as _compose:
        config.compose(**kwargs)
    _compose.assert_called_once_with(
        configs=list(map(Path, pathstrs)),
        realize=False,
        output_file=None if output_file is None else Path(output_file),
        input_format=input_format,
        output_format=output_format,
    )


@mark.parametrize(
    ("classname", "f"),
    [
        ("FieldTableConfig", config.get_fieldtable_config),
        ("INIConfig", config.get_ini_config),
        ("NMLConfig", config.get_nml_config),
        ("SHConfig", config.get_sh_config),
        ("YAMLConfig", config.get_yaml_config),
    ],
)
def test_api_config__get_config(classname, f):
    kwargs: dict = dict(config={})
    with patch.object(config, classname) as constructor:
        f(**kwargs)
    constructor.assert_called_once_with(**kwargs)


def test_api_config_realize():
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


def test_api_config_realize__update_config_from_stdin():
    with raises(UWError) as e:
        config.realize(input_config={}, output_file="output.yaml", update_format="yaml")
    assert str(e.value) == "Set stdin_ok=True to permit read from stdin"


def test_api_config_realize__update_config_none():
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


def test_api_config_realize_to_dict():
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
        **{**kwargs, "output_file": Path(os.devnull), "output_format": FORMAT.yaml}
    )


@mark.parametrize("cfg", [{"foo": "bar"}, YAMLConfig(config={"foo": "bar"})])
def test_api_config_validate__config_data(cfg):
    kwargs: dict = {"schema_file": "schema-file", "config_data": cfg}
    with patch.object(config, "_validate_external") as _validate_external:
        assert config.validate(**kwargs) is True
        _validate_external.side_effect = UWConfigError()
        assert config.validate(**kwargs) is False
    _validate_external.assert_called_with(
        schema_file=Path(kwargs["schema_file"]),
        desc="config",
        config_data=kwargs["config_data"],
        config_path=None,
    )


@mark.parametrize("cast", [str, Path])
def test_api_config__validate_config_path(cast, tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.dump({}))
    kwargs: dict = {"schema_file": "schema-file", "config_path": cast(cfg)}
    with patch.object(config, "_validate_external", return_value=True) as _validate_external:
        assert config.validate(**kwargs)
    _validate_external.assert_called_once_with(
        schema_file=Path(kwargs["schema_file"]), desc="config", config_data=None, config_path=cfg
    )
