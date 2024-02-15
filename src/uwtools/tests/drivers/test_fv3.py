# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
FV3 driver tests.
"""
import datetime as dt
from functools import partial
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import PropertyMock, patch

import pytest
import yaml
from pytest import fixture

from uwtools.drivers import fv3
from uwtools.tests.support import logged, validator, with_del, with_set

# Fixtures


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


# Driver fixtures


@fixture
def config(tmp_path):
    return {
        "fv3": {
            "domain": "global",
            "execution": {"executable": "fv3"},
            "lateral_boundary_conditions": {
                "interval_hours": 1,
                "offset": 0,
                "path": str(tmp_path / "f{forecast_hour}"),
            },
            "length": 1,
            "run_dir": str(tmp_path),
        }
    }


@fixture
def config_file(config, tmp_path):
    path = tmp_path / "config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    return path


@fixture
def driverobj(config_file, cycle):
    return fv3.FV3(config_file=config_file, cycle=cycle, batch=True)


# Driver tests


def test_FV3(driverobj):
    assert isinstance(driverobj, fv3.FV3)


def test_FV3_dry_run(config_file, cycle):
    with patch.object(fv3, "dryrun") as dryrun:
        driverobj = fv3.FV3(config_file=config_file, cycle=cycle, batch=True, dry_run=True)
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_FV3_boundary_files(driverobj):
    ns = (0, 1)
    links = [driverobj._rundir / "INPUT" / f"gfs_bndy.tile7.{n:03d}.nc" for n in ns]
    assert not any(link.is_file() for link in links)
    for n in ns:
        (driverobj._rundir / f"f{n}").touch()
    driverobj.boundary_files()
    assert all(link.is_symlink() for link in links)


def test_FV3_diag_table(driverobj):
    src = driverobj._rundir / "diag_table.in"
    src.touch()
    driverobj._driver_config["diag_table"] = src
    dst = driverobj._rundir / "diag_table"
    assert not dst.is_file()
    driverobj.diag_table()
    assert dst.is_file()


def test_FV3_diag_table_warn(caplog, driverobj):
    driverobj.diag_table()
    assert logged(caplog, "No 'diag_table' defined in config")


def test_FV3_field_table(driverobj):
    src = driverobj._rundir / "field_table.in"
    with open(src, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    dst = driverobj._rundir / "field_table"
    assert not dst.is_file()
    driverobj._driver_config["field_table"] = {"base_file": src}
    driverobj.field_table()
    assert dst.is_file()


@pytest.mark.parametrize(
    "key,task,test",
    [("files_to_copy", "files_copied", "is_file"), ("files_to_link", "files_linked", "is_symlink")],
)
def test_FV3_files_copied(config, cycle, key, task, test, tmp_path):
    atm, sfc = "gfs.t%sz.atmanl.nc", "gfs.t%sz.sfcanl.nc"
    atm_cfg_dst, sfc_cfg_dst = [x % "{{ cycle.strftime('%H') }}" for x in [atm, sfc]]
    atm_cfg_src, sfc_cfg_src = [str(tmp_path / (x + ".in")) for x in [atm_cfg_dst, sfc_cfg_dst]]
    config["fv3"].update({key: {atm_cfg_dst: atm_cfg_src, sfc_cfg_dst: sfc_cfg_src}})
    path = tmp_path / "config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    driverobj = fv3.FV3(config_file=path, cycle=cycle, batch=True)
    atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    for src in (atm_src, sfc_src):
        src.touch()
    getattr(driverobj, task)()
    assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


def test_FV3_model_configure(driverobj):
    src = driverobj._rundir / "model_configure.in"
    with open(src, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    dst = driverobj._rundir / "model_configure"
    assert not dst.is_file()
    driverobj._driver_config["model_configure"] = {"base_file": src}
    driverobj.model_configure()
    assert dst.is_file()


def test_FV3_namelist_file(driverobj):
    src = driverobj._rundir / "input.nml.in"
    with open(src, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    dst = driverobj._rundir / "input.nml"
    assert not dst.is_file()
    driverobj._driver_config["namelist_file"] = {"base_file": src}
    driverobj.namelist_file()
    assert dst.is_file()


def test_FV3_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        boundary_files=D,
        diag_table=D,
        field_table=D,
        files_copied=D,
        files_linked=D,
        model_configure=D,
        namelist_file=D,
        restart_directory=D,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_FV3_restart_directory(driverobj):
    path = driverobj._rundir / "RESTART"
    assert not path.is_dir()
    driverobj.restart_directory()
    assert path.is_dir()


def test_FV3_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_FV3_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_FV3_runscript(driverobj):
    dst = driverobj._rundir / "runscript"
    assert not dst.is_file()
    driverobj._driver_config["execution"].update(
        {
            "batchargs": {"walltime": "01:10:00"},
            "envcmds": ["cmd1", "cmd2"],
            "mpicmd": "runit",
            "threads": 8,
        }
    )
    driverobj._config["platform"] = {"account": "me", "scheduler": "slurm"}
    driverobj.runscript()
    with open(dst, "r", encoding="utf-8") as f:
        lines = f.read().split("\n")
    # Check directives:
    assert "#SBATCH --account=me" in lines
    assert "#SBATCH --time=01:10:00" in lines
    # Check environment variables:
    assert "export ESMF_RUNTIME_COMPLIANCECHECK=OFF:depth=4" in lines
    assert "export KMP_AFFINITY=scatter" in lines
    assert "export MPI_TYPE_DEPTH=20" in lines
    assert "export OMP_NUM_THREADS=8" in lines
    assert "export OMP_STACKSIZE=512m" in lines
    # Check environment commands:
    assert "cmd1" in lines
    assert "cmd2" in lines
    # Check execution:
    assert "runit fv3" in lines
    assert "test $? -eq 0 && touch %s/done" % driverobj._rundir


def test_FV3__run_via_batch_submission(driverobj):
    runscript = driverobj._runscript_path
    with patch.object(driverobj, "provisioned_run_directory") as prd:
        with patch.object(fv3.FV3, "_scheduler", new_callable=PropertyMock) as scheduler:
            driverobj._run_via_batch_submission()
            scheduler().submit_job.assert_called_once_with(
                runscript=runscript, submit_file=Path(f"{runscript}.submit")
            )
        prd.assert_called_once_with()


def test_FV3__run_via_local_execution(driverobj):
    with patch.object(driverobj, "provisioned_run_directory") as prd:
        with patch.object(fv3, "execute") as execute:
            driverobj._run_via_local_execution()
            execute.assert_called_once_with(
                cmd="{x} >{x}.out 2>&1".format(x=driverobj._runscript_path),
                cwd=driverobj._rundir,
                log_output=True,
            )
        prd.assert_called_once_with()


def test_FV3__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["fv3"]


def test_FV3__resources(driverobj):
    account = "me"
    scheduler = "slurm"
    walltime = "01:10:00"
    driverobj._driver_config["execution"].update({"batchargs": {"walltime": walltime}})
    driverobj._config["platform"] = {"account": account, "scheduler": scheduler}
    assert driverobj._resources == {
        "account": account,
        "rundir": driverobj._rundir,
        "scheduler": scheduler,
        "walltime": walltime,
    }


def test_FV3__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript"


def test_FV3__taskanme(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z FV3 foo"


def test_FV3__validate(driverobj):
    driverobj._validate()


# Schema fixtures


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
    return partial(validator, "fv3", "properties", "fv3", "properties")


# Schema tests


def test_fv3_schema_defs_filesToStage():
    errors = validator("fv3", "$defs", "filesToStage")
    # The input must be an dict:
    assert "is not of type 'object'" in errors([])
    # A str -> str dict is ok:
    assert not errors({"file1": "/path/to/file1", "file2": "/path/to/file2"})
    # An empty dict is not allowed:
    assert "does not have enough properties" in errors({})
    # Non-string values are not allowed:
    assert "True is not of type 'string'" in errors({"file1": True})


def test_fv3_schema_defs_namelist():
    errors = validator("fv3", "$defs", "namelist")
    # Basic correctness (see also namelist_names_values test):
    assert not errors({"namelist": {"string": "foo"}})
    # Needs at least one value:
    assert "does not have enough properties" in errors({})
    # Must be a mapping:
    assert "[] is not of type 'object'" in errors([])


def test_fv3_schema_defs_namelist_names_values():
    errors = validator("fv3", "$defs", "namelist_names_values")
    # Basic correctness:
    assert not errors(
        {"array": [1, 2, 3], "boolean": True, "float": 3.14, "integer": 88, "string": "foo"}
    )
    # Other types are not allowed:
    errormsg = "%s is not of type 'array', 'boolean', 'number', 'string'"
    assert errormsg % "None" in errors({"nonetype": None})
    assert errormsg % "{}" in errors({"dict": {}})
    # Needs at least one value:
    assert "does not have enough properties" in errors({})
    # Must be a mapping:
    assert "[] is not of type 'object'" in errors([])


def test_fv3_schema():
    d = {
        "domain": "regional",
        "execution": {"executable": "fv3"},
        "lateral_boundary_conditions": {"interval_hours": 1, "offset": 0, "path": "/tmp/file"},
        "length": 3,
        "run_dir": "/tmp",
    }
    errors = validator("fv3", "properties", "fv3")
    # Basic correctness:
    assert not errors(d)
    # Some top-level keys are required:
    for key in ("domain", "execution", "lateral_boundary_conditions", "length", "run_dir"):
        assert f"'{key}' is a required property" in errors(with_del(d, key))
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
        }
    )
    # Additional top-level keys are not allowed:
    assert "Additional properties are not allowed" in errors({**d, "foo": "bar"})


def test_fv3_schema_diag_table(fcstprop):
    errors = fcstprop("diag_table")
    # String value is ok:
    assert not errors("/path/to/file")
    # Anything else is not:
    assert "88 is not of type 'string'" in errors(88)


def test_fv3_schema_domain(fcstprop):
    errors = fcstprop("domain")
    # There is a fixed set of domain values:
    assert "'foo' is not one of ['global', 'regional']" in errors("foo")


def test_fv3_schema_execution(fcstprop):
    d = {"executable": "fv3"}
    batchargs = {"batchargs": {"queue": "string", "walltime": "string"}}
    mpiargs = {"mpiargs": ["--flag1", "--flag2"]}
    threads = {"threads": 32}
    errors = fcstprop("execution")
    # Basic correctness:
    assert not errors(d)
    # batchargs may optionally be specified:
    assert not errors({**d, **batchargs})
    # mpiargs may be optionally specified:
    assert not errors({**d, **mpiargs})
    # threads may optionally be specified:
    assert not errors({**d, **threads})
    # All properties are ok:
    assert not errors({**d, **batchargs, **mpiargs, **threads})
    # Additional properties are not allowed:
    assert "Additional properties are not allowed" in errors(
        {**d, **mpiargs, **threads, "foo": "bar"}
    )


def test_fv3_schema_execution_batchargs(fcstprop):
    errors = fcstprop("execution", "properties", "batchargs")
    # Basic correctness, empty map is ok:
    assert not errors({})
    # Managed properties are fine:
    assert not errors({"queue": "string", "walltime": "string"})
    # But so are unknown ones:
    assert not errors({"--foo": 88})
    # It just has to be a map:
    assert "[] is not of type 'object'" in errors([])


def test_fv3_schema_execution_executable(fcstprop):
    errors = fcstprop("execution", "properties", "executable")
    # String value is ok:
    assert not errors("fv3.exe")
    # Anything else is not:
    assert "88 is not of type 'string'" in errors(88)


def test_fv3_schema_execution_mpiargs(fcstprop):
    errors = fcstprop("execution", "properties", "mpiargs")
    # Basic correctness:
    assert not errors(["string1", "string2"])
    # mpiargs may be empty:
    assert not errors([])
    # String values are expected:
    assert "88 is not of type 'string'" in errors(["string1", 88])


def test_fv3_schema_execution_threads(fcstprop):
    errors = fcstprop("execution", "properties", "threads")
    # threads must be non-negative, and an integer:
    assert not errors(0)
    assert not errors(4)
    assert "-1 is less than the minimum of 0" in errors(-1)
    assert "3.14 is not of type 'integer'" in errors(3.14)


def test_fv3_schema_field_table(fcstprop, field_table_vals):
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


def test_fv3_schema_field_table_update_values(fcstprop, field_table_vals):
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


def test_fv3_schema_files_to_copy():
    test_fv3_schema_defs_filesToStage()


def test_fv3_schema_files_to_link():
    test_fv3_schema_defs_filesToStage()


def test_fv3_schema_lateral_boundary_conditions(fcstprop):
    d = {
        "interval_hours": 1,
        "offset": 0,
        "path": "/some/path",
    }
    errors = fcstprop("lateral_boundary_conditions")
    # Basic correctness:
    assert not errors(d)
    # All lateral_boundary_conditions items are required:
    assert "'interval_hours' is a required property" in errors(with_del(d, "interval_hours"))
    assert "'offset' is a required property" in errors(with_del(d, "offset"))
    assert "'path' is a required property" in errors(with_del(d, "path"))
    # interval_hours must be an integer of at least 1:
    assert "0 is less than the minimum of 1" in errors(with_set(d, 0, "interval_hours"))
    assert "'s' is not of type 'integer'" in errors(with_set(d, "s", "interval_hours"))
    # offset must be an integer of at least 0:
    assert "-1 is less than the minimum of 0" in errors(with_set(d, -1, "offset"))
    assert "'s' is not of type 'integer'" in errors(with_set(d, "s", "offset"))
    # path must be a string:
    assert "88 is not of type 'string'" in errors(with_set(d, 88, "path"))


def test_fv3_schema_length(fcstprop):
    errors = fcstprop("length")
    # Positive int is ok:
    assert not errors(6)
    # Zero is not ok:
    assert "0 is less than the minimum of 1" in errors(0)
    # A negative number is not ok:
    assert "-1 is less than the minimum of 1" in errors(-1)
    # Something other than an int is not ok:
    assert "'a string' is not of type 'integer'" in errors("a string")


def test_fv3_schema_model_configure(fcstprop):
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


def test_fv3_schema_model_configure_update_values(fcstprop):
    errors = fcstprop("model_configure", "properties", "update_values")
    # boolean, number, and string values are ok:
    assert not errors({"bool": True, "int": 88, "float": 3.14, "string": "foo"})
    # Other types are not, e.g.:
    assert "None is not of type 'boolean', 'number', 'string'" in errors({"null": None})
    # At least one entry is required:
    assert "does not have enough properties" in errors({})


def test_fv3_schema_namelist(fcstprop):
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


def test_fv3_schema_namelist_update_values(fcstprop):
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


def test_fv3_schema_run_dir(fcstprop):
    errors = fcstprop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)
