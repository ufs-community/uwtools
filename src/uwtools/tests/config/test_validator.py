# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.validator module.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Tuple
from unittest.mock import patch

from pytest import fixture

from uwtools.config import validator
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.logging import log
from uwtools.tests.support import logged, regex_logged
from uwtools.utils.file import resource_pathobj

# Fixtures


@fixture
def assets(config, schema, tmp_path) -> Tuple[Path, Path, YAMLConfig]:
    config_file = tmp_path / "config.yaml"
    schema_file = tmp_path / "schema.yaml"
    write_as_json(config, config_file)
    write_as_json(schema, schema_file)
    return schema_file, config_file, YAMLConfig(config_file)


@fixture
def config(tmp_path) -> Dict[str, Any]:
    return {
        "color": "blue",
        "dir": str(tmp_path),
        "number": 88,
        "sub": {
            "dir": str(tmp_path),
        },
    }


@fixture
def schema() -> Dict[str, Any]:
    return {
        "properties": {
            "color": {
                "enum": ["blue", "red"],
                "type": "string",
            },
            "dir": {
                "format": "uri",
                "type": "string",
            },
            "number": {"type": "number"},
            "sub": {
                "properties": {
                    "dir": {
                        "format": "uri",
                        "type": "string",
                    },
                    "type": "object",
                },
            },
        },
        "type": "object",
    }


# Helpers


def write_as_json(data: Dict[str, Any], path: Path) -> Path:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


# Test functions


def test_validate_yaml_config_fail_bad_enum_val(assets, caplog):
    log.setLevel(logging.INFO)
    schema_file, _, cfgobj = assets
    cfgobj["color"] = "yellow"  # invalid enum value
    assert not validator.validate_yaml_config(schema_file=schema_file, config=cfgobj)
    assert any(x for x in caplog.records if "1 schema-validation error found" in x.message)
    assert any(x for x in caplog.records if "'yellow' is not one of" in x.message)


def test_validate_yaml_config_fail_bad_number_val(assets, caplog):
    log.setLevel(logging.INFO)
    schema_file, _, cfgobj = assets
    cfgobj["number"] = "string"  # invalid number value
    assert not validator.validate_yaml_config(schema_file=schema_file, config=cfgobj)
    assert any(x for x in caplog.records if "1 schema-validation error found" in x.message)
    assert any(x for x in caplog.records if "'string' is not of type 'number'" in x.message)


def test_validate_yaml_config_pass(assets):
    schema_file, _, cfgobj = assets
    assert validator.validate_yaml_config(schema_file=schema_file, config=cfgobj)


@fixture
def rocoto_assets():
    schema_file = resource_pathobj("rocoto.jsonschema")
    kwargs = {"schema_file": schema_file, "config_file": "/not/used"}
    config = {
        "workflow": {
            "cycledef": [{"spec": "202209290000 202209300000 06:00:00"}],
            "log": "/some/path/to/&FOO;",
            "tasks": {
                "metatask": {
                    "var": {"member": "foo bar baz"},
                    "task": {
                        "cores": 88,
                        "command": "some-command",
                        "walltime": "00:01:00",
                        "dependency": {
                            "taskdep": {
                                "attrs": {
                                    "task": "hello",
                                },
                            },
                        },
                    },
                },
            },
        }
    }
    return kwargs, config


def test_validate_yaml_file_rocoto_invalid_dependency_bool(rocoto_assets, caplog):
    kwargs, config = rocoto_assets
    config["workflow"]["tasks"]["metatask"]["task"]["dependency"].update(
        {"maybe": {"taskdep": {"attrs": {"task": "hello"}}}}
    )
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        YAMLConfig().data = config
        assert not validator.validate_yaml_file(**kwargs)
        assert regex_logged(caplog, "'maybe' does not match any of the regexes")


def test_validate_yaml_file_rocoto_invalid_dependency_no_task(rocoto_assets, caplog):
    kwargs, config = rocoto_assets
    del config["workflow"]["tasks"]["metatask"]["task"]["dependency"]["taskdep"]["attrs"]["task"]
    config["workflow"]["tasks"]["metatask"]["task"]["dependency"]["taskdep"]["attrs"][
        "state"
    ] = "RUNNING"
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        YAMLConfig().data = config
        assert not validator.validate_yaml_file(**kwargs)
        assert logged(caplog, "'task' is a required property")


def test_validate_yaml_file_rocoto_invalid_no_command(rocoto_assets, caplog):
    kwargs, config = rocoto_assets
    del config["workflow"]["tasks"]["metatask"]["task"]["command"]
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        YAMLConfig().data = config
        assert not validator.validate_yaml_file(**kwargs)
        assert logged(caplog, "'command' is a required property")


def test_validate_yaml_file_rocoto_invalid_no_task(rocoto_assets, caplog):
    kwargs, config = rocoto_assets
    del config["workflow"]["tasks"]["metatask"]["task"]
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        YAMLConfig().data = config
        assert not validator.validate_yaml_file(**kwargs)
        assert logged(caplog, "{'var': {'member': 'foo bar baz'}} does not have enough properties")


def test_validate_yaml_file_rocoto_invalid_no_var(rocoto_assets, caplog):
    kwargs, config = rocoto_assets
    del config["workflow"]["tasks"]["metatask"]["var"]
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        YAMLConfig().data = config
        assert not validator.validate_yaml_file(**kwargs)
        assert logged(caplog, "'var' is a required property")


def test_validate_yaml_file_rocoto_invalid_required_stderr(rocoto_assets, caplog):
    kwargs, config = rocoto_assets
    config["workflow"]["tasks"]["metatask"]["task"].update({"stdout": "hello"})
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        YAMLConfig().data = config
        assert not validator.validate_yaml_file(**kwargs)
        assert logged(caplog, "'stderr' is a required property")


def test_validate_yaml_file_rocoto_invalid_type(rocoto_assets, caplog):
    kwargs, config = rocoto_assets
    config["workflow"]["tasks"]["metatask"]["task"]["cores"] = "string"
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        YAMLConfig().data = config
        assert not validator.validate_yaml_file(**kwargs)
        assert logged(caplog, "'string' is not of type 'integer'")


def test_validate_yaml_file_rocoto_invalid_walltime_pattern(rocoto_assets, caplog):
    kwargs, config = rocoto_assets
    badval = "0x:01:00"
    config["workflow"]["tasks"]["metatask"]["task"]["walltime"] = badval
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        YAMLConfig().data = config
        assert not validator.validate_yaml_file(**kwargs)
        assert logged(caplog, f"'{badval}' is not valid under any of the given schemas")


def test_validate_yaml_file_rocoto_valid(rocoto_assets):
    kwargs, config = rocoto_assets
    with patch.object(validator, "YAMLConfig") as YAMLConfig:
        YAMLConfig().data = config
        assert validator.validate_yaml_file(**kwargs)


def test__validation_errors_bad_enum_value(config, schema):
    config["color"] = "yellow"
    assert len(validator._validation_errors(config, schema)) == 1


def test__validation_errors_bad_number_value(config, schema):
    config["number"] = "string"
    assert len(validator._validation_errors(config, schema)) == 1


def test__validation_errors_pass(config, schema):
    assert not validator._validation_errors(config, schema)
