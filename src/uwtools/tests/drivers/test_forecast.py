# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for forecast driver.
"""
import datetime as dt
import logging
import os
from functools import partial
from pathlib import Path
from unittest.mock import ANY, patch

import pytest
from pytest import fixture, raises

from uwtools import scheduler
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers import forecast
from uwtools.drivers.driver import Driver
from uwtools.drivers.forecast import FV3Forecast
from uwtools.logging import log
from uwtools.tests.support import compare_files, fixture_path, logged, validator, with_del, with_set
from uwtools.types import ExistAct


def test_batch_script():
    expected = """
#SBATCH --account=user_account
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --qos=batch
#SBATCH --time=00:01:00
KMP_AFFINITY=scatter
OMP_NUM_THREADS=1
OMP_STACKSIZE=512m
MPI_TYPE_DEPTH=20
ESMF_RUNTIME_COMPLIANCECHECK=OFF:depth=4
srun --export=NONE test_exec.py
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
    FV3Forecast.create_directory_structure(rundir, ExistAct.delete)
    assert (rundir / "RESTART").is_dir()

    # Create a file in the run directory.
    test_file = rundir / "test.txt"
    test_file.touch()
    assert test_file.is_file()

    # Test delete behavior when run directory exists. Test file should be gone
    # since old run directory was deleted.
    FV3Forecast.create_directory_structure(rundir, ExistAct.delete)
    assert (rundir / "RESTART").is_dir()
    assert not test_file.is_file()

    # Test rename behavior when run directory exists.
    FV3Forecast.create_directory_structure(rundir, ExistAct.rename)
    copy_directory = next(tmp_path.glob("%s_*" % rundir.name))
    assert (copy_directory / "RESTART").is_dir()

    # Test quit behavior when run directory exists.
    with raises(SystemExit) as pytest_wrapped_e:
        FV3Forecast.create_directory_structure(rundir, ExistAct.quit)
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
    _create_user_updated_config.assert_called_with(
        config_class=YAMLConfig, config_values={}, output_path=outfile
    )


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


def test_create_namelist_with_base_file(create_namelist_assets, tmp_path):
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


@pytest.mark.parametrize("section", ["static", "cycle_dependent"])
@pytest.mark.parametrize("link_files", [True, False])
def test_stage_files(tmp_path, section, link_files):
    """
    Tests that files from static or cycle_dependent sections of the config obj are being staged
    (copied or linked) to the run directory.
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
    for dst_rel_path, src_paths in files_to_stage.items():
        if isinstance(src_paths, list):
            dst_paths = [run_directory / dst_rel_path / os.path.basename(sp) for sp in src_paths]
            assert all(link_or_file(d_fn) for d_fn in dst_paths)
        else:
            assert link_or_file(run_directory / dst_rel_path)
    if section == "cycle_dependent":
        assert link_or_file(run_directory / "INPUT" / "gfs_bndy.tile7.006.nc")


@fixture
def fv3_run_assets(tmp_path):
    batch_script = tmp_path / "batch.sh"
    config_file = fixture_path("forecast.yaml")
    config = YAMLConfig(config_file)
    config["forecast"]["run_dir"] = tmp_path.as_posix()
    config["forecast"]["cycle_dependent"] = {"foo-file": str(tmp_path / "foo")}
    config["forecast"]["static"] = {"static-foo-file": str(tmp_path / "foo")}
    return batch_script, config_file, config.data["forecast"]


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


def test_run_direct(fv3_mpi_assets, fv3_run_assets):
    _, config_file, config = fv3_run_assets
    expected_command = " ".join(fv3_mpi_assets)
    with patch.object(FV3Forecast, "_validate", return_value=True):
        with patch.object(forecast, "execute") as execute:
            execute.return_value = (True, "")
            fcstobj = FV3Forecast(config_file=config_file)
            with patch.object(fcstobj, "_config", config):
                fcstobj.run(cycle=dt.datetime.now())
            execute.assert_called_once_with(cmd=expected_command, cwd=ANY, log_output=True)


@pytest.mark.parametrize("with_batch_script", [True, False])
def test_FV3Forecast_run_dry_run(caplog, fv3_mpi_assets, fv3_run_assets, with_batch_script):
    log.setLevel(logging.INFO)
    batch_script, config_file, config = fv3_run_assets
    if with_batch_script:
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
        batch_script = None
        expected_lines = [" ".join(fv3_mpi_assets)]

    with patch.object(FV3Forecast, "_validate", return_value=True):
        fcstobj = FV3Forecast(config_file=config_file, dry_run=True, batch_script=batch_script)
        with patch.object(fcstobj, "_config", config):
            fcstobj.run(cycle=dt.datetime.now())
    for line in expected_lines:
        assert logged(caplog, line)


@pytest.mark.parametrize(
    "vals", [(True, "_run_via_batch_submission"), (False, "_run_via_local_execution")]
)
def test_FV3Forecast_run(fv3_run_assets, vals):
    batch_script, config_file, _ = fv3_run_assets
    use_batch, helper_method = vals
    fcstobj = FV3Forecast(config_file=config_file, batch_script=batch_script if use_batch else None)
    with patch.object(fcstobj, helper_method) as helper:
        helper.return_value = (True, None)
        assert fcstobj.run(cycle=dt.datetime.now()) is True
        helper.assert_called_once_with()


def test_FV3Forecast__run_via_batch_submission(fv3_run_assets):
    batch_script, config_file, config = fv3_run_assets
    fcstobj = FV3Forecast(config_file=config_file, batch_script=batch_script)
    with patch.object(fcstobj, "_config", config):
        with patch.object(scheduler, "execute") as execute:
            with patch.object(Driver, "_create_user_updated_config"):
                execute.return_value = (True, "")
                success, lines = fcstobj._run_via_batch_submission()
                assert success is True
                assert lines[0] == "Batch script:"
                execute.assert_called_once_with(cmd=ANY, cwd=ANY)


def test_FV3Forecast__run_via_local_execution(fv3_run_assets):
    _, config_file, config = fv3_run_assets
    fcstobj = FV3Forecast(config_file=config_file)
    with patch.object(fcstobj, "_config", config):
        with patch.object(forecast, "execute") as execute:
            execute.return_value = (True, "")
            success, lines = fcstobj._run_via_local_execution()
            assert success is True
            assert lines[0] == "Command:"
            execute.assert_called_once_with(cmd=ANY, cwd=ANY, log_output=True)


# Schema tests


@fixture
def field_table_vals():
    return (
        {
            "foo": {
                "longname": "foofoo",
                "profile_type": {"name": "fixed", "surface_value": 1},
                "units": "cubits",
            }
        },
        {
            "bar": {
                "longname": "barbar",
                "profile_type": {"name": "profile", "surface_value": 2, "top_value": 3},
                "units": "rods",
            }
        },
    )


@fixture
def fcstprop():
    return partial(validator, "FV3Forecast.jsonschema", "properties", "forecast", "properties")


def test_FV3Forecast_schema_filesToStage():
    errors = validator("FV3Forecast.jsonschema", "$defs", "filesToStage")
    # The input must be an dict:
    assert "is not of type 'object'" in errors([])
    # A str -> str dict is ok:
    assert not errors({"file1": "/path/to/file1", "file2": "/path/to/file2"})
    # An empty dict is not allowed:
    assert "does not have enough properties" in errors({})
    # Non-string values are not allowed:
    assert "True is not of type 'string'" in errors({"file1": True})


def test_FV3Forecast_schema_forecast():
    d = {"domain": "regional", "executable": "fv3", "length": 3, "run_dir": "/tmp"}
    errors = validator("FV3Forecast.jsonschema", "properties", "forecast")
    # Basic correctness:
    assert not errors(d)
    # Some top-level keys are required:
    assert "'domain' is a required property" in errors(with_del(d, "domain"))
    assert "'executable' is a required property" in errors(with_del(d, "executable"))
    assert "'length' is a required property" in errors(with_del(d, "length"))
    assert "'run_dir' is a required property" in errors(with_del(d, "run_dir"))
    # Some top-level keys are optional:
    assert not errors(
        {
            **d,
            "diag_table": "/path",
            "field_table": {"base_file": "/path"},
            "files_to_copy": {"fn": "/path"},
            "files_to_link": {"fn": "/path"},
            "model_configure": {"base_file": "/path"},
            "namelist": {"base_file": "/path"},
            "runtime_info": {},
        }
    )
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**d, "foo": "bar"})


def test_FV3Forecast_schema_forecast_diag_table(fcstprop):
    errors = fcstprop("diag_table")
    # String value is ok:
    assert not errors("/path/to/file")
    # Anything else is not:
    assert "88 is not of type 'string'" in errors(88)


def test_FV3Forecast_schema_forecast_domain(fcstprop):
    errors = fcstprop("domain")
    # There is a fixed set of domain values:
    assert "'foo' is not one of ['global', 'regional']" in errors("foo")


def test_FV3Forecast_schema_forecast_executable(fcstprop):
    errors = fcstprop("executable")
    # String value is ok:
    assert not errors("fv3.exe")
    # Anything else is not:
    assert "88 is not of type 'string'" in errors(88)


def test_FV3Forecast_schema_forecast_field_table(fcstprop, field_table_vals):
    val, _ = field_table_vals
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": val}
    errors = fcstprop("field_table")
    # Just base_file is ok:
    assert not errors(base_file)
    # Just update_values is ok:
    assert not errors(update_values)
    # A combination of base_file and update_values is ok:
    assert not errors({**base_file, **update_values})
    # At least one is required:
    assert "is not valid" in errors({})


def test_FV3Forecast_schema_forecast_field_table_update_values(fcstprop, field_table_vals):
    val1, val2 = field_table_vals
    errors = fcstprop("field_table", "properties", "update_values")
    # A "fixed" profile-type entry is ok:
    assert not errors(val1)
    # A "profile" profile-type entry is ok:
    assert not errors(val2)
    # A combination of two valid entries is ok:
    assert not errors({**val1, **val2})
    # At least one entry is required:
    assert "does not have enough properties" in errors({})
    # longname is required:
    assert "'longname' is a required property" in errors(with_del(val1, "foo", "longname"))
    # longname must be a string:
    assert "88 is not of type 'string'" in errors(with_set(val1, 88, "foo", "longname"))
    # units is required:
    assert "'units' is a required property" in errors(with_del(val1, "foo", "units"))
    # units must be a string:
    assert "88 is not of type 'string'" in errors(with_set(val1, 88, "foo", "units"))
    # profile_type is required:
    assert "'profile_type' is a required property" in errors(with_del(val1, "foo", "profile_type"))
    # profile_type name has to be "fixed" or "profile":
    assert "'bogus' is not one of ['fixed', 'profile']" in errors(
        with_set(val1, "bogus", "foo", "profile_type", "name")
    )
    # surface_value is required:
    assert "'surface_value' is a required property" in errors(
        with_del(val1, "foo", "profile_type", "surface_value")
    )
    # surface_value is numeric:
    assert "'a string' is not of type 'number'" in errors(
        with_set(val1, "a string", "foo", "profile_type", "surface_value")
    )
    # top_value is required if name is "profile":
    assert "'top_value' is a required property" in errors(
        with_del(val2, "bar", "profile_type", "top_value")
    )
    # top_value is numeric:
    assert "'a string' is not of type 'number'" in errors(
        with_set(val2, "a string", "bar", "profile_type", "top_value")
    )


def test_FV3Forecast_schema_forecast_files_to_copy():
    test_FV3Forecast_schema_filesToStage()


def test_FV3Forecast_schema_forecast_files_to_link():
    test_FV3Forecast_schema_filesToStage()


def test_FV3Forecast_schema_forecast_length(fcstprop):
    errors = fcstprop("length")
    # Positive int is ok:
    assert not errors(6)
    # Zero is not ok:
    assert "0 is less than the minimum of 1" in errors(0)
    # A negative number is not ok:
    assert "-1 is less than the minimum of 1" in errors(-1)
    # Something other than an int is not ok:
    assert "'a string' is not of type 'integer'" in errors("a string")


def test_FV3Forecast_schema_forecast_model_configure(fcstprop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"foo": 88}}
    errors = fcstprop("model_configure")
    # Just base_file is ok:
    assert not errors(base_file)
    # But base_file must be a string:
    assert "88 is not of type 'string'" in errors({"base_file": 88})
    # Just update_values is ok:
    assert not errors(update_values)
    # A combination of base_file and update_values is ok:
    assert not errors({**base_file, **update_values})
    # At least one is required:
    assert "is not valid" in errors({})


def test_FV3Forecast_schema_forecast_model_configure_update_values(fcstprop):
    errors = fcstprop("model_configure", "properties", "update_values")
    # boolean, number, and string values are ok:
    assert not errors({"bool": True, "int": 88, "float": 3.14, "string": "foo"})
    # Other types are not, e.g.:
    assert "None is not of type 'boolean', 'number', 'string'" in errors({"null": None})
    # At least one entry is required:
    assert "does not have enough properties" in errors({})


def test_FV3Forecast_schema_forecast_namelist(fcstprop):
    base_file = {"base_file": "/some/path"}
    update_values = {"update_values": {"nml": {"var": "val"}}}
    errors = fcstprop("namelist")
    # Just base_file is ok:
    assert not errors(base_file)
    # base_file must be a string:
    assert "88 is not of type 'string'" in errors({"base_file": 88})
    # Just update_values is ok:
    assert not errors(update_values)
    # A combination of base_file and update_values is ok:
    assert not errors({**base_file, **update_values})
    # At least one is required:
    assert "is not valid" in errors({})


def test_FV3Forecast_schema_forecast_namelist_update_values(fcstprop):
    errors = fcstprop("namelist", "properties", "update_values")
    # array, boolean, number, and string values are ok:
    assert not errors(
        {"nml": {"array": [1, 2, 3], "bool": True, "int": 88, "float": 3.14, "string": "foo"}}
    )
    # Other types are not, e.g.:
    assert "None is not of type 'array', 'boolean', 'number', 'string'" in errors(
        {"nml": {"null": None}}
    )
    # At least one namelist entry is required:
    assert "does not have enough properties" in errors({})
    # At least one val/var pair ir required:
    assert "does not have enough properties" in errors({"nml": {}})


def test_FV3Forecast_schema_forecast_run_dir(fcstprop):
    errors = fcstprop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


def test_FV3Forecast_schema_forecast_runtime_info(fcstprop):
    mpi_args = {"mpi_args": ["--flag1", "--flag2"]}
    threads = {"threads": 32}
    errors = fcstprop("runtime_info")
    # mpi_args is a list of strings:
    assert not errors(mpi_args)
    # mpi_args may be empty:
    assert not errors({"mpi_args": []})
    # String values are expected:
    assert "88 is not of type 'string'" in errors({"mpi_args": [88]})
    # threads must be non-negative, and an integer:
    assert not errors(threads)
    assert not errors({"threads": 0})
    assert "-1 is less than the minimum of 0" in errors({"threads": -1})
    assert "3.14 is not of type 'integer'" in errors({"threads": 3.14})
    # Both properties are ok:
    assert not errors({**mpi_args, **threads})
    # Additional properties are not allowed:
    assert "Additional properties are not allowed" in errors({**mpi_args, **threads, "foo": "bar"})


def test_FV3Forecast_schema_platform():
    d = {"account": "me", "mpicmd": "cmd", "scheduler": "slurm"}
    errors = validator("FV3Forecast.jsonschema", "properties", "platform")
    # Basic correctness:
    assert not errors(d)
    # At least mpicmd is required:
    assert "'mpicmd' is a required property" in errors({})
    # Extra top-level keys are forbidden:
    assert "Additional properties are not allowed" in errors(with_set(d, "bar", "foo"))
    # There is a fixed set of supported schedulers:
    assert "'foo' is not one of ['lsf', 'pbs', 'slurm']" in errors(with_set(d, "foo", "scheduler"))
    # account and scheduler are optional:
    assert not errors({"mpicmd": "cmd"})
    # account is required if scheduler is specified:
    assert "'account' is a dependency of 'scheduler'" in errors(with_del(d, "account"))


def test_FV3Forecast_schema_preprocessing():
    d = {
        "lateral_boundary_conditions": {
            "interval_hours": 1,
            "offset": 0,
            "output_file_path": "/some/path",
        }
    }
    errors = validator("FV3Forecast.jsonschema", "properties", "preprocessing")
    # Basic correctness:
    assert not errors(d)
    assert "'lateral_boundary_conditions' is a required property" in errors({})
    # All lateral_boundary_conditions items are required:
    assert "'interval_hours' is a required property" in errors(
        with_del(d, "lateral_boundary_conditions", "interval_hours")
    )
    assert "'offset' is a required property" in errors(
        with_del(d, "lateral_boundary_conditions", "offset")
    )
    assert "'output_file_path' is a required property" in errors(
        with_del(d, "lateral_boundary_conditions", "output_file_path")
    )
    # interval_hours must be an integer of at least 1:
    assert "0 is less than the minimum of 1" in errors(
        with_set(d, 0, "lateral_boundary_conditions", "interval_hours")
    )
    assert "'a string' is not of type 'integer'" in errors(
        with_set(d, "a string", "lateral_boundary_conditions", "interval_hours")
    )
    # offset must be an integer of at least 0:
    assert "-1 is less than the minimum of 0" in errors(
        with_set(d, -1, "lateral_boundary_conditions", "offset")
    )
    assert "'a string' is not of type 'integer'" in errors(
        with_set(d, "a string", "lateral_boundary_conditions", "offset")
    )
    # output_file_path must be a string:
    assert "88 is not of type 'string'" in errors(
        with_set(d, 88, "lateral_boundary_conditions", "output_file_path")
    )
