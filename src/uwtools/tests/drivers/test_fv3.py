# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for FV3 driver.
"""
import datetime as dt
import logging

# import os
from pathlib import Path
from unittest.mock import patch  # ANY

import pytest
from pytest import fixture  # , raises

# from uwtools import scheduler
from uwtools.config.formats.yaml import YAMLConfig

# from uwtools.drivers import fv3
from uwtools.drivers.driver import Driver
from uwtools.drivers.fv3 import FV3
from uwtools.logging import log
from uwtools.tests.support import fixture_path, logged, validator  # compare_files

# from uwtools.types import ExistAct


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


# def test_batch_script():
#     expected = """
# #SBATCH --account=user_account
# #SBATCH --nodes=1
# #SBATCH --ntasks-per-node=1
# #SBATCH --qos=batch
# #SBATCH --time=00:01:00
# KMP_AFFINITY=scatter
# OMP_NUM_THREADS=1
# OMP_STACKSIZE=512m
# MPI_TYPE_DEPTH=20
# ESMF_RUNTIME_COMPLIANCECHECK=OFF:depth=4
# srun --export=NONE test_exec.py
# """.strip()
#     config_file = fixture_path("forecast.yaml")
#     with patch.object(Driver, "_validate", return_value=True):
#         forecast = FV3Forecast(config_file=config_file)
#     assert forecast.batch_script().content() == expected


def test_schema_file(cycle):
    """
    Tests that the schema is properly defined with a file value.
    """
    config_file = fixture_path("forecast.yaml")
    with patch.object(Driver, "_validate", return_value=True):
        forecast = FV3(config_file=config_file, cycle=cycle)
    path = Path(forecast.schema_file)
    assert path.is_file()


# def test_create_model_configure(cycle, tmp_path):
#     """
#     Test that providing a YAML base input file and a config file will create and update YAML
#     config file.
#     """
#     config_file = fixture_path("fruit_config_similar_for_fcst.yaml")
#     base_file = fixture_path("fruit_config.yaml")
#     fcst_config_file = tmp_path / "fcst.yml"
#     fcst_config = YAMLConfig(config_file)
#     fcst_config["forecast"]["model_configure"]["base_file"] = base_file
#     fcst_config.dump(fcst_config_file)
#     output_file = (tmp_path / "test_config_from_yaml.yaml").as_posix()
#     with patch.object(FV3Forecast, "_validate", return_value=True):
#         forecast_obj = FV3Forecast(config_file=fcst_config_file, cycle=cycle)
#     forecast_obj.create_model_configure(output_file)
#     expected = YAMLConfig(base_file)
# expected.update_values(YAMLConfig(config_file)["forecast"]["model_configure"]["update_values"])
#     expected_file = tmp_path / "expected_yaml.yaml"
#     expected.dump(expected_file)
#     assert compare_files(expected_file, output_file)


@fixture
def create_field_table_update_obj():
    return YAMLConfig(fixture_path("FV3_GFS_v16_update.yaml"))


# def test_create_field_table_with_base_file(create_field_table_update_obj, cycle, tmp_path):
#     """
#     Tests create_field_table method with optional base file.
#     """
#     base_file = fixture_path("FV3_GFS_v16.yaml")
#     outfldtbl_file = tmp_path / "field_table_two.FV3_GFS"
#     expected = fixture_path("field_table_from_base.FV3_GFS")
#     config_file = tmp_path / "fcst.yaml"
#     forecast_config = create_field_table_update_obj
#     forecast_config["forecast"]["field_table"]["base_file"] = base_file
#     forecast_config.dump(config_file)
#     FV3Forecast(config_file=config_file, cycle=cycle).create_field_table(outfldtbl_file)
#     assert compare_files(expected, outfldtbl_file)


# def test_create_field_table_without_base_file(cycle, tmp_path):
#     """
#     Tests create_field_table without optional base file.
#     """
#     outfldtbl_file = tmp_path / "field_table_one.FV3_GFS"
#     expected = fixture_path("field_table_from_input.FV3_GFS")
#     config_file = fixture_path("FV3_GFS_v16_update.yaml")
#     FV3Forecast(config_file=config_file, cycle=cycle).create_field_table(outfldtbl_file)
#     assert compare_files(expected, outfldtbl_file)


# def test_create_model_configure_call_private(cycle, tmp_path):
#     basefile = str(tmp_path / "base.yaml")
#     infile = fixture_path("forecast.yaml")
#     outfile = str(tmp_path / "out.yaml")
#     for path in infile, basefile:
#         Path(path).touch()
#     with patch.object(Driver, "_create_user_updated_config") as _create_user_updated_config:
#         with patch.object(FV3Forecast, "_validate", return_value=True):
#             FV3Forecast(config_file=infile, cycle=cycle).create_model_configure(outfile)
#     _create_user_updated_config.assert_called_with(
#         config_class=YAMLConfig, config_values={}, output_path=outfile
#     )


@fixture
def create_namelist_assets(tmp_path):
    update_values = {
        "salad": {
            "base": "kale",
            "fruit": "banana",
            "vegetable": "tomato",
            "how_many": 12,
            "dressing": "balsamic",
        }
    }
    return update_values, tmp_path / "create_out.nml"


@pytest.mark.skip("PM FIXME")
def test_create_namelist_with_base_file(create_namelist_assets, cycle, tmp_path):
    """
    Tests create_namelist method with optional base file.
    """
    update_values, outnml_file = create_namelist_assets
    base_file = fixture_path("simple3.nml")
    fcst_config = {
        "forecast": {
            "namelist": {
                "base_file": base_file,
                "update_values": update_values,
            },
        },
    }
    fcst_config_file = tmp_path / "fcst.yml"
    YAMLConfig.dump_dict(cfg=fcst_config, path=fcst_config_file)
    FV3(config_file=fcst_config_file, cycle=cycle).create_namelist(outnml_file)
    expected = """
&salad
    base = 'kale'
    fruit = 'banana'
    vegetable = 'tomato'
    how_many = 12
    dressing = 'balsamic'
    toppings = ,
    extras = 0
    dessert = .false.
    appetizer = ,
/
""".lstrip()
    with open(outnml_file, "r", encoding="utf-8") as out_file:
        assert out_file.read() == expected


@pytest.mark.skip("PM FIXME")
def test_create_namelist_without_base_file(create_namelist_assets, cycle, tmp_path):
    """
    Tests create_namelist method without optional base file.
    """
    update_values, outnml_file = create_namelist_assets
    fcst_config = {
        "forecast": {
            "namelist": {
                "update_values": update_values,
            },
        },
    }
    fcst_config_file = tmp_path / "fcst.yml"
    YAMLConfig.dump_dict(cfg=fcst_config, path=fcst_config_file)
    FV3(config_file=fcst_config_file, cycle=cycle).create_namelist(outnml_file)
    expected = """
&salad
    base = 'kale'
    fruit = 'banana'
    vegetable = 'tomato'
    how_many = 12
    dressing = 'balsamic'
/
""".lstrip()
    with open(outnml_file, "r", encoding="utf-8") as out_file:
        assert out_file.read() == expected


def test_forecast_run_cmd(cycle):
    """
    Tests that the command to be used to run the forecast executable was built successfully.
    """
    config_file = fixture_path("forecast.yaml")
    with patch.object(FV3, "_validate", return_value=True):
        fcstobj = FV3(config_file=config_file, cycle=cycle)
        srun_expected = "srun --export=NONE test_exec.py"
        fcstobj._config["runtime_info"]["mpi_args"] = ["--export=NONE"]
        assert srun_expected == fcstobj.run_cmd()
        mpirun_expected = "mpirun -np 4 test_exec.py"
        fcstobj._experiment_config["platform"]["mpicmd"] = "mpirun"
        fcstobj._config["runtime_info"]["mpi_args"] = ["-np", 4]
        assert mpirun_expected == fcstobj.run_cmd()
        fcstobj._experiment_config["platform"]["mpicmd"] = "mpiexec"
        fcstobj._config["runtime_info"]["mpi_args"] = [
            "-n",
            4,
            "-ppn",
            8,
            "--cpu-bind",
            "core",
            "-depth",
            2,
        ]
        mpiexec_expected = "mpiexec -n 4 -ppn 8 --cpu-bind core -depth 2 test_exec.py"
        assert mpiexec_expected == fcstobj.run_cmd()


# @pytest.mark.parametrize("section", ["static", "cycle_dependent"])
# @pytest.mark.parametrize("link_files", [True, False])
# def test_stage_files(tmp_path, section, link_files):
#     """
#     Tests that files from static or cycle_dependent sections of the config obj are being staged
#     (copied or linked) to the run directory.
#     """
#     run_directory = tmp_path / "run"
#     src_directory = tmp_path / "src"
#     files_to_stage = YAMLConfig(fixture_path("expt_dir.yaml"))[section]
#     # Fix source paths so that they are relative to our test temp directory and
#     # create the test files.
#     src_directory.mkdir()
#     for dst_fn, src_path in files_to_stage.items():
#         if isinstance(src_path, list):
#             files_to_stage[dst_fn] = [str(src_directory / Path(sp).name) for sp in src_path]
#         else:
#             fixed_src_path = src_directory / Path(src_path).name
#             files_to_stage[dst_fn] = str(fixed_src_path)
#             fixed_src_path.touch()
#     # Test that none of the destination files exist yet:
#     for dst_fn in files_to_stage.keys():
#         assert not (run_directory / dst_fn).is_file()
#     # Ask a forecast object to stage the files to the run directory:
#     FV3.create_directory_structure(run_directory)
#     FV3.stage_files(run_directory, files_to_stage, link_files=link_files)
#     # Test that all of the destination files now exist:
#     link_or_file = Path.is_symlink if link_files else Path.is_file
#     for dst_rel_path, src_paths in files_to_stage.items():
#         if isinstance(src_paths, list):
#             dst_paths = [run_directory / dst_rel_path / os.path.basename(sp) for sp in src_paths]
#             assert all(link_or_file(d_fn) for d_fn in dst_paths)
#         else:
#             assert link_or_file(run_directory / dst_rel_path)
#     if section == "cycle_dependent":
#         assert link_or_file(run_directory / "INPUT" / "gfs_bndy.tile7.006.nc")


@fixture
def fv3_run_assets(tmp_path):
    config_file = fixture_path("forecast.yaml")
    config = YAMLConfig(config_file)
    config["forecast"]["run_dir"] = tmp_path.as_posix()
    config["forecast"]["cycle_dependent"] = {"foo-file": str(tmp_path / "foo")}
    config["forecast"]["static"] = {"static-foo-file": str(tmp_path / "foo")}
    return config_file, config.data["forecast"]


@fixture
def fv3_mpi_assets():
    return [
        "KMP_AFFINITY=scatter",
        "OMP_NUM_THREADS=1",
        "OMP_STACKSIZE=512m",
        "MPI_TYPE_DEPTH=20",
        "ESMF_RUNTIME_COMPLIANCECHECK=OFF:depth=4",
        "srun --export=NONE test_exec.py",
    ]


# def test_run_direct(cycle, fv3_mpi_assets, fv3_run_assets):
#     _, config_file, config = fv3_run_assets
#     expected_command = " ".join(fv3_mpi_assets)
#     with patch.object(FV3, "_validate", return_value=True):
#         with patch.object(forecast, "execute") as execute:
#             execute.return_value = (True, "")
#             fcstobj = FV3(config_file=config_file, cycle=cycle)
#             with patch.object(fcstobj, "_config", config):
#                 fcstobj.run()
#             execute.assert_called_once_with(cmd=expected_command, cwd=ANY, log_output=True)


@pytest.mark.skip("PM FIXME")
@pytest.mark.parametrize("batch", [True, False])
def test_FV3_run_dry_run(batch, caplog, cycle, fv3_mpi_assets, fv3_run_assets):
    log.setLevel(logging.INFO)
    config_file, config = fv3_run_assets
    if batch:
        batch_components = [
            "#!/bin/bash",
            "#SBATCH --account=user_account",
            "#SBATCH --nodes=1",
            "#SBATCH --ntasks-per-node=1",
            "#SBATCH --qos=batch",
            "#SBATCH --time=00:01:00",
        ] + fv3_mpi_assets
        expected_lines = batch_components
    else:
        expected_lines = [" ".join(fv3_mpi_assets)]
    with patch.object(FV3, "_validate", return_value=True):
        fcstobj = FV3(config_file=config_file, cycle=cycle, dry_run=True, batch=batch)
        with patch.object(fcstobj, "_config", config):
            fcstobj.run()
    for line in expected_lines:
        assert logged(caplog, line)


@pytest.mark.skip("PM FIXME")
@pytest.mark.parametrize(
    "batch,method", [(True, "_run_via_batch_submission"), (False, "_run_via_local_execution")]
)
def test_FV3_run(batch, cycle, fv3_run_assets, method):
    config_file, _ = fv3_run_assets
    fcstobj = FV3(config_file=config_file, cycle=cycle, batch=batch)
    with patch.object(fcstobj, method) as helper:
        helper.return_value = (True, None)
        assert fcstobj.run() is True
        helper.assert_called_once_with()


# @pytest.mark.skip("PM FIXME")
# def test_FV3__run_via_batch_submission(cycle, fv3_run_assets):
#     batch_script, config_file, config = fv3_run_assets
#     fcstobj = FV3(config_file=config_file, cycle=cycle, batch_script=batch_script)
#     with patch.object(fcstobj, "_config", config):
#         with patch.object(scheduler, "execute") as execute:
#             with patch.object(Driver, "_create_user_updated_config"):
#                 execute.return_value = (True, "")
#                 success, lines = fcstobj._run_via_batch_submission()
#                 assert success is True
#                 assert lines[0] == "Batch script:"
#                 execute.assert_called_once_with(cmd=ANY, cwd=ANY)


# @pytest.mark.skip("PM FIXME")
# def test_FV3__run_via_local_execution(cycle, fv3_run_assets):
#     _, config_file, config = fv3_run_assets
#     fcstobj = FV3(config_file=config_file, cycle=cycle)
#     with patch.object(fcstobj, "_config", config):
#         with patch.object(forecast, "execute") as execute:
#             execute.return_value = (True, "")
#             success, lines = fcstobj._run_via_local_execution()
#             assert success is True
#             assert lines[0] == "Command:"
#             execute.assert_called_once_with(cmd=ANY, cwd=ANY, log_output=True)


# Schema tests


def test_FV3_schema_filesToStage():
    errors = validator("fv3.jsonschema", "$defs", "filesToStage")
    # The input must be an dict:
    assert "is not of type 'object'" in errors([])
    # A str -> str dict is ok:
    assert not errors({"file1": "/path/to/file1", "file2": "/path/to/file2"})
    # A str -> List[str] dict is ok:
    assert not errors({"dir": ["/path/to/file1", "/path/to/file2"]})
    # An empty dict is not allowed:
    assert "does not have enough properties" in errors({})
    # Non-string values are not allowed:
    assert "not valid" in errors({"file1": True})
    # Non-string list elements are not allowed:
    assert "not valid" in errors({"dir": [88]})
