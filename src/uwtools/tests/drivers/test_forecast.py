# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for forecast driver.
"""
import datetime as dt
import logging
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools.config.core import NMLConfig, YAMLConfig
from uwtools.drivers import forecast
from uwtools.drivers.driver import Driver
from uwtools.drivers.forecast import FV3Forecast
from uwtools.tests.support import compare_files, fixture_path


def test_batch_script():
    expected = """
#SBATCH --account=user_account
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --qos=batch
#SBATCH --time=00:01:00
KMP_AFFINITY=scatter
OMP_NUM_THREADS=1
OMP_STACKSIZE=1
MPI_TYPE_DEPTH=20
ESMF_RUNTIME_COMPLIANCECHECK=OFF:depth=4
srun --export=None test_exec.py
""".strip()
    config_file = fixture_path("forecast.yaml")
    with patch.object(Driver, "_validate", return_value=True):
        forecast = FV3Forecast(config_file=config_file)
    assert forecast.batch_script().content() == expected


def test_schema_file():
    """
    Tests that the schema is properly defined with a file value.
    """

    config_file = fixture_path("forecast.yaml")
    with patch.object(Driver, "_validate", return_value=True):
        forecast = FV3Forecast(config_file=config_file)

    path = Path(forecast.schema_file)
    assert path.is_file()


def test_create_model_configure(tmp_path):
    """
    Test that providing a YAML base input file and a config file will create and update YAML config
    file.
    """

    config_file = fixture_path("fruit_config_similar_for_fcst.yaml")
    base_file = fixture_path("fruit_config.yaml")
    fcst_config_file = tmp_path / "fcst.yml"

    fcst_config = YAMLConfig(config_file)
    fcst_config["forecast"]["model_configure"]["base_file"] = base_file
    fcst_config.dump(fcst_config_file)

    output_file = (tmp_path / "test_config_from_yaml.yaml").as_posix()
    with patch.object(FV3Forecast, "_validate", return_value=True):
        forecast_obj = FV3Forecast(config_file=fcst_config_file)
    forecast_obj.create_model_configure(output_file)
    expected = YAMLConfig(base_file)
    expected.update_values(YAMLConfig(config_file)["forecast"]["model_configure"]["update_values"])
    expected_file = tmp_path / "expected_yaml.yaml"
    expected.dump(expected_file)
    assert compare_files(expected_file, output_file)


def test_create_directory_structure(tmp_path):
    """
    Tests create_directory_structure method given a directory.
    """

    rundir = tmp_path / "rundir"

    # Test delete behavior when run directory does not exist.
    FV3Forecast.create_directory_structure(rundir, "delete")
    assert (rundir / "RESTART").is_dir()

    # Create a file in the run directory.
    test_file = rundir / "test.txt"
    test_file.touch()
    assert test_file.is_file()

    # Test delete behavior when run directory exists. Test file should be gone
    # since old run directory was deleted.
    FV3Forecast.create_directory_structure(rundir, "delete")
    assert (rundir / "RESTART").is_dir()
    assert not test_file.is_file()

    # Test rename behavior when run directory exists.
    FV3Forecast.create_directory_structure(rundir, "rename")
    copy_directory = next(tmp_path.glob("%s_*" % rundir.name))
    assert (copy_directory / "RESTART").is_dir()

    # Test quit behavior when run directory exists.
    with raises(SystemExit) as pytest_wrapped_e:
        FV3Forecast.create_directory_structure(rundir, "quit")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1


@fixture
def create_field_table_update_obj():
    return YAMLConfig(fixture_path("FV3_GFS_v16_update.yaml"))


def test_create_field_table_with_base_file(create_field_table_update_obj, tmp_path):
    """
    Tests create_field_table method with optional base file.
    """
    base_file = fixture_path("FV3_GFS_v16.yaml")
    outfldtbl_file = tmp_path / "field_table_two.FV3_GFS"
    expected = fixture_path("field_table_from_base.FV3_GFS")
    config_file = tmp_path / "fcst.yaml"
    forecast_config = create_field_table_update_obj
    forecast_config["forecast"]["field_table"]["base_file"] = base_file
    forecast_config.dump(config_file)
    FV3Forecast(config_file).create_field_table(outfldtbl_file)
    assert compare_files(expected, outfldtbl_file)


def test_create_field_table_without_base_file(tmp_path):
    """
    Tests create_field_table without optional base file.
    """
    outfldtbl_file = tmp_path / "field_table_one.FV3_GFS"
    expected = fixture_path("field_table_from_input.FV3_GFS")
    config_file = fixture_path("FV3_GFS_v16_update.yaml")
    FV3Forecast(config_file).create_field_table(outfldtbl_file)
    assert compare_files(expected, outfldtbl_file)


def test_create_directory_structure_bad_existing_act():
    with raises(ValueError):
        FV3Forecast.create_directory_structure(run_directory="/some/path", exist_act="foo")


def test_create_model_configure_call_private(tmp_path):
    basefile = str(tmp_path / "base.yaml")
    infile = fixture_path("forecast.yaml")
    outfile = str(tmp_path / "out.yaml")
    for path in infile, basefile:
        Path(path).touch()
    with patch.object(Driver, "_create_user_updated_config") as _create_user_updated_config:
        with patch.object(FV3Forecast, "_validate", return_value=True):
            FV3Forecast(config_file=infile).create_model_configure(outfile)
    assert _create_user_updated_config.call_args.kwargs["config_class"] == YAMLConfig
    assert _create_user_updated_config.call_args.kwargs["config_values"] is None
    assert _create_user_updated_config.call_args.kwargs["output_path"] == outfile


@fixture
def create_namelist_assets(tmp_path):
    return NMLConfig(fixture_path("simple.nml")), tmp_path / "create_out.nml"


def test_create_namelist_with_base_file(create_namelist_assets, tmp_path):
    """
    Tests create_namelist method with optional base file.
    """
    update_obj, outnml_file = create_namelist_assets
    base_file = fixture_path("simple3.nml")
    fcst_config = {
        "forecast": {
            "namelist": {
                "base_file": base_file,
                "update_values": update_obj.data,
            },
        },
    }
    fcst_config_file = tmp_path / "fcst.yml"
    YAMLConfig.dump_dict(cfg=fcst_config, path=fcst_config_file)
    FV3Forecast(fcst_config_file).create_namelist(outnml_file)
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


def test_create_namelist_without_base_file(create_namelist_assets, tmp_path):
    """
    Tests create_namelist method without optional base file.
    """
    update_obj, outnml_file = create_namelist_assets
    fcst_config = {
        "forecast": {
            "namelist": {
                "update_values": update_obj.data,
            },
        },
    }
    fcst_config_file = tmp_path / "fcst.yml"
    YAMLConfig.dump_dict(cfg=fcst_config, path=fcst_config_file)
    FV3Forecast(fcst_config_file).create_namelist(outnml_file)
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


def test_forecast_run_cmd():
    """
    Tests that the command to be used to run the forecast executable was built successfully.
    """
    config_file = fixture_path("forecast.yaml")
    with patch.object(FV3Forecast, "_validate", return_value=True):
        fcstobj = FV3Forecast(config_file=config_file)
        hera_expected = "srun --export=ALL test_exec.py"
        assert hera_expected == fcstobj.run_cmd("--export=ALL")
        cheyenne_expected = "mpirun -np 4 test_exec.py"

        fcstobj._experiment_config["platform"]["mpicmd"] = "mpirun"
        assert cheyenne_expected == fcstobj.run_cmd("-np", 4)

        fcstobj._experiment_config["platform"]["mpicmd"] = "mpiexec"
        wcoss2_expected = "mpiexec -n 4 -ppn 8 --cpu-bind core -depth 2 test_exec.py"
        assert wcoss2_expected == fcstobj.run_cmd(
            "-n",
            4,
            "-ppn",
            8,
            "--cpu-bind",
            "core",
            "-depth",
            2,
        )


@pytest.mark.parametrize("section", ["static", "cycledep"])
@pytest.mark.parametrize("link_files", [True, False])
def test_stage_files(tmp_path, section, link_files):
    """
    Tests that files from static or cycledep sections of the config obj are being staged (copied or
    linked) to the run directory.
    """

    run_directory = tmp_path / "run"
    src_directory = tmp_path / "src"
    files_to_stage = YAMLConfig(fixture_path("expt_dir.yaml"))[section]
    # Fix source paths so that they are relative to our test temp directory and
    # create the test files.
    src_directory.mkdir()
    for dst_fn, src_path in files_to_stage.items():
        if isinstance(src_path, list):
            files_to_stage[dst_fn] = [str(src_directory / Path(sp).name) for sp in src_path]
        else:
            fixed_src_path = src_directory / Path(src_path).name
            files_to_stage[dst_fn] = str(fixed_src_path)
            fixed_src_path.touch()
    # Test that none of the destination files exist yet:
    for dst_fn in files_to_stage.keys():
        assert not (run_directory / dst_fn).is_file()
    # Ask a forecast object to stage the files to the run directory:
    FV3Forecast.create_directory_structure(run_directory)
    FV3Forecast.stage_files(run_directory, files_to_stage, link_files=link_files)
    # Test that all of the destination files now exist:
    link_or_file = Path.is_symlink if link_files else Path.is_file
    for dst_fn, src_paths in files_to_stage.items():
        if isinstance(src_paths, list):
            dst_fns = [run_directory / dst_fn / os.path.basename(sp) for sp in src_paths]
            assert all(link_or_file(d_fn) for d_fn in dst_fns)
        else:
            assert link_or_file(run_directory / dst_fn)


@fixture
def fv3_run_assets(tmp_path):
    batch_script = tmp_path / "batch.sh"
    config_file = fixture_path("forecast.yaml")
    config = YAMLConfig(config_file)
    config["forecast"]["run_dir"] = tmp_path.as_posix()
    config["forecast"]["cycle-dependent"] = {"foo-file": str(tmp_path / "foo")}
    config["forecast"]["static"] = {"static-foo-file": str(tmp_path / "foo")}
    return batch_script, config_file, config.data


def test_run_direct(fv3_run_assets):
    _, config_file, config = fv3_run_assets
    expected_command = """
KMP_AFFINITY=scatter
OMP_NUM_THREADS=1
OMP_STACKSIZE=1
MPI_TYPE_DEPTH=20
ESMF_RUNTIME_COMPLIANCECHECK=OFF:depth=4
srun --export=None test_exec.py"""
    expected_command = expected_command.replace("\n", " ")
    with patch.object(FV3Forecast, "_validate", return_value=True):
        with patch.object(forecast.subprocess, "run") as sprun:
            fcstobj = FV3Forecast(config_file=config_file)
            with patch.object(fcstobj, "_experiment_config", config):
                fcstobj.run(cycle=dt.datetime.now())
            sprun.assert_called_once_with(
                expected_command,
                stderr=subprocess.STDOUT,
                check=False,
                shell=True,
            )


def test_FV3Forecast__config_deleter():
    config_file = fixture_path("forecast.yaml")
    with patch.object(Driver, "_validate", return_value=True):
        forecast = FV3Forecast(config_file=config_file)

    assert forecast._config
    del forecast._config
    assert not forecast._config


def test_FV3Forecast__config_setter():
    config_file = fixture_path("forecast.yaml")
    with patch.object(Driver, "_validate", return_value=True):
        forecast = FV3Forecast(config_file=config_file)
    new_config = {"foo": 1, "bar": 2}
    forecast._config = new_config
    assert forecast._config_data == new_config
    assert forecast._config == new_config


@pytest.mark.parametrize("with_batch_script", [True, False])
def test_FV3Forecast_run_dry_run(caplog, fv3_run_assets, with_batch_script):
    logging.getLogger().setLevel(logging.INFO)
    batch_script, config_file, config = fv3_run_assets
    run_expected = """KMP_AFFINITY=scatter
OMP_NUM_THREADS=1
OMP_STACKSIZE=1
MPI_TYPE_DEPTH=20
ESMF_RUNTIME_COMPLIANCECHECK=OFF:depth=4
srun --export=None test_exec.py
"""
    if with_batch_script:
        run_expected = (
            """#!/bin/bash
#SBATCH --account=user_account
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --qos=batch
#SBATCH --time=00:01:00
"""
            + run_expected.strip()
        )
    else:
        batch_script = None
        run_expected = run_expected.replace("\n", " ").strip()

    with patch.object(FV3Forecast, "_validate", return_value=True):
        fcstobj = FV3Forecast(config_file=config_file, dry_run=True, batch_script=batch_script)
        with patch.object(fcstobj, "_experiment_config", config):
            print(fcstobj._config)
            fcstobj.run(cycle=dt.datetime.now())
    assert run_expected in caplog.text


def test_run_submit(fv3_run_assets):
    batch_script, config_file, config = fv3_run_assets
    with patch.object(FV3Forecast, "_validate", return_value=True):
        with patch.object(forecast.subprocess, "run") as sprun:
            fcstobj = FV3Forecast(config_file=config_file, batch_script=batch_script)
            with patch.object(fcstobj, "_experiment_config", config):
                fcstobj.run(cycle=dt.datetime.now())
            sprun.assert_called_once_with(
                f"sbatch {batch_script}",
                stderr=subprocess.STDOUT,
                check=False,
                shell=True,
            )
