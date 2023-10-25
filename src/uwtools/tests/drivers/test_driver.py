# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.drivers.driver module.
"""

import datetime
import glob
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pytest import fixture, raises

from uwtools.config.core import YAMLConfig
from uwtools.drivers import driver
from uwtools.drivers.driver import Driver
from uwtools.tests.support import compare_files, fixture_path, logged


class ConcreteDriver(Driver):
    """
    Driver subclass for testing purposes.
    """

    def batch_script(self):
        pass

    def output(self):
        pass

    def requirements(self):
        pass

    def resources(self) -> Mapping:
        return {}

    def run(self, cycle: datetime.date) -> bool:
        return True

    @property
    def schema_file(self) -> str:
        return ""


@fixture
def configs():
    config_good = """
platform:
  WORKFLOW_MANAGER: rocoto
"""
    config_bad = """
platform:
  WORKFLOW_MANAGER: 20
"""
    return config_good, config_bad


@fixture
def mpi_config():
    return yaml.safe_load(
        """
platform:
  mpicmd: srun
component:
  exec_name: foo
  runtime_info:
    mpi_args:
      - bar
"""
    )


@fixture
def schema():
    return """
{
  "title": "workflow config",
  "description": "This document is to validate user-defined FV3 forecast config files",
  "type": "object",
  "properties": {
    "platform": {
      "description": "attributes of the platform",
      "type": "object",
      "properties": {
        "WORKFLOW_MANAGER": {
          "type": "string",
          "enum": [
            "rocoto",
            "none"
          ]
        }
      }
    }
  }
}
""".strip()


def test_create_directory_structure(tmp_path):
    run_dir = tmp_path / "run"
    with patch.object(Driver, "_create_run_directory") as _create_run_directory:
        Driver.create_directory_structure(run_dir)
    _create_run_directory.assert_called_once_with(run_dir, "delete")


def test_create_directory_structure_bad_existing_act():
    with raises(ValueError):
        Driver.create_directory_structure(run_directory="/some/path", exist_act="foo")


def test_run_cmd_expected(mpi_config, tmp_path):
    config_file = tmp_path / "config.yaml"
    YAMLConfig.dump_dict(config_file, mpi_config)
    with patch.object(Driver, "_validate", return_value=True):
        driver = ConcreteDriver(config_file=config_file)
    driver._config = driver._experiment_config["component"]
    assert driver.run_cmd() == "srun bar foo"


def test_run_cmd_no_runtime_info(mpi_config, tmp_path):
    config_file = tmp_path / "config.yaml"
    del mpi_config["component"]["runtime_info"]
    YAMLConfig.dump_dict(config_file, mpi_config)
    with patch.object(Driver, "_validate", return_value=True):
        driver = ConcreteDriver(config_file=config_file)
    driver._config = driver._experiment_config["component"]
    with raises(KeyError):
        driver.run_cmd()


def test_scheduler():
    config_file = fixture_path("fruit_config.yaml")
    with patch.object(Driver, "_validate", return_value=True):
        concretedriver = ConcreteDriver(config_file=config_file)
        # pylint: disable=pointless-statement
        with patch.object(driver.JobScheduler, "get_scheduler") as get_scheduler:
            concretedriver.scheduler
    _get_scheduler.assert_called_once_with({})


@pytest.mark.parametrize("link_files", [True, False])
def test_stage_files(tmp_path, link_files):
    """
    Tests that files from static or cycle-dependent sections of the config obj are being staged
    (copied or linked) to the run directory.
    """

    run_directory = tmp_path / "run"
    src_directory = tmp_path / "src"
    files_to_stage = yaml.safe_load(
        """
foo.yaml: some/foo/on/disk/foo.yml
bar: somewhere/bar.txt
./:
  - a/file/with/same_name.x
  - another/file/with/same/name.f
"""
    )
    # Fix source paths so that they are relative to our test temp directory and
    # create the test files.
    src_directory.mkdir()
    for dst_fn, src_path in files_to_stage.items():
        if isinstance(src_path, list):
            files_to_stage[dst_fn] = [str(src_directory / Path(sp).name) for sp in src_path]
            for src_file in files_to_stage[dst_fn]:
                Path(src_file).touch()
        else:
            fixed_src_path = src_directory / Path(src_path).name
            files_to_stage[dst_fn] = str(fixed_src_path)
            fixed_src_path.touch()
    # Test that none of the destination files exist yet:
    for dst_fn in files_to_stage.keys():
        assert not (run_directory / dst_fn).is_file()
    # Ask a forecast object to stage the files to the run directory:
    Driver.create_directory_structure(run_directory)
    Driver.stage_files(run_directory, files_to_stage, link_files=link_files)
    # Test that all of the destination files now exist:
    link_or_file = Path.is_symlink if link_files else Path.is_file
    for dst_rel_path, src_paths in files_to_stage.items():
        if isinstance(src_paths, list):
            dst_paths = [run_directory / dst_rel_path / os.path.basename(sp) for sp in src_paths]
            assert all(link_or_file(d_fn) for d_fn in dst_paths)
        else:
            assert link_or_file(run_directory / dst_rel_path)


@pytest.mark.parametrize("exist_act", ["delete", "rename"])
def test__create_run_directory_exists(exist_act, tmp_path):
    run_dir = tmp_path / "run"
    Driver._create_run_directory(run_dir, exist_act)
    Driver._create_run_directory(run_dir, exist_act)
    run_dirs = len(glob.glob((tmp_path / "run*").as_posix()))
    assert run_dirs == 1 if exist_act == "delete" else run_dirs == 2


@pytest.mark.parametrize("exist_act", ["delete", "rename"])
def test__create_run_directory_handle_existing_call(exist_act, tmp_path):
    run_dir = tmp_path / "run"
    with patch.object(driver, "handle_existing") as handle_existing:
        Driver._create_run_directory(run_dir, exist_act)
    handle_existing.called_once_with(run_dir, exist_act)


def test__create_run_directory_quit(tmp_path):
    run_dir = tmp_path / "run"
    Driver._create_run_directory(run_dir, "quit")
    with raises(SystemExit):
        Driver._create_run_directory(run_dir, "quit")


@fixture
def update_config():
    config_file = fixture_path("fruit_config.yaml")
    return yaml.safe_load(
        f"""
base_file: {config_file}
update_values:
  nuts: almonds
  dressing: vinaigrette
"""
    )


def test__create_user_updated_config_base_file(tmp_path, update_config):
    expected_file = tmp_path / "expected.yml"
    base_config = YAMLConfig(fixture_path("fruit_config.yaml"))
    base_config.update_values(update_config["update_values"])
    YAMLConfig.dump_dict(path=expected_file, cfg=base_config.data)

    output_file = tmp_path / "output.yml"
    Driver._create_user_updated_config(YAMLConfig, update_config, output_file)
    assert compare_files(expected_file, output_file)


def test__create_user_updated_config_no_base_file(tmp_path, update_config):
    expected_file = tmp_path / "expected.yml"
    expected_config = update_config["update_values"]
    YAMLConfig.dump_dict(path=expected_file, cfg=expected_config)

    output_file = tmp_path / "output.nml"
    del update_config["base_file"]
    Driver._create_user_updated_config(YAMLConfig, update_config, output_file)
    assert compare_files(expected_file, output_file)


@pytest.mark.parametrize("valid", [True, False])
def test_validation(caplog, configs, schema, tmp_path, valid):
    config_good, config_bad = configs
    config_file = str(tmp_path / "config.yaml")
    with open(config_file, "w", encoding="utf-8") as f:
        print(config_good if valid else config_bad, file=f)
    schema_file = str(tmp_path / "test.jsonschema")
    with open(schema_file, "w", encoding="utf-8") as f:
        print(schema, file=f)
    with patch.object(ConcreteDriver, "schema_file", new=schema_file):
        logging.getLogger().setLevel(logging.INFO)
        ConcreteDriver(config_file=config_file)
        if valid:
            assert logged(caplog, "0 schema-validation errors found")
        else:
            assert logged(caplog, "2 schema-validation errors found")
