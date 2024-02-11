# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
FV3 driver tests.
"""
import datetime as dt
from functools import partial

import pytest
from pytest import fixture

from uwtools.tests.support import validator, with_del, with_set

# Class FV3 tests


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


# def test_FV3__schema_file(cycle):
#     config_file = fixture_path("fv3.yaml")
#     with patch.object(Driver, "_validate", return_value=True):
#         forecast = FV3(config_file=config_file, cycle=cycle)
#     path = Path(forecast._schema_file)
#     assert path.is_file()


# def test_forecast__run_cmd(cycle):
#     config_file = fixture_path("fv3.yaml")
#     with patch.object(FV3, "_validate", return_value=True):
#         fcstobj = FV3(config_file=config_file, cycle=cycle)
#         srun_expected = "srun --export=NONE test_exec.py"
#         fcstobj._driver_config["execution"]["mpiargs"] = ["--export=NONE"]
#         assert srun_expected == fcstobj._run_cmd
#         mpirun_expected = "mpirun -np 4 test_exec.py"
#         fcstobj._driver_config["execution"]["mpicmd"] = "mpirun"
#         fcstobj._driver_config["execution"]["mpiargs"] = ["-np", 4]
#         assert mpirun_expected == fcstobj._run_cmd
#         fcstobj._driver_config["execution"]["mpicmd"] = "mpiexec"
#         mpiargs = ["-n", 4, "-ppn", 8, "--cpu-bind", "core", "-depth", 2]
#         fcstobj._driver_config["execution"]["mpiargs"] = mpiargs
#         mpiexec_expected = "mpiexec -n 4 -ppn 8 --cpu-bind core -depth 2 test_exec.py"
#         assert mpiexec_expected == fcstobj._run_cmd


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
    return partial(validator, "fv3.jsonschema", "properties", "fv3", "properties")


def test_fv3_schema_filesToStage():
    errors = validator("fv3.jsonschema", "$defs", "filesToStage")
    # The input must be an dict:
    assert "is not of type 'object'" in errors([])
    # A str -> str dict is ok:
    assert not errors({"file1": "/path/to/file1", "file2": "/path/to/file2"})
    # An empty dict is not allowed:
    assert "does not have enough properties" in errors({})
    # Non-string values are not allowed:
    assert "True is not of type 'string'" in errors({"file1": True})


def test_fv3_schema_forecast():
    d = {
        "domain": "regional",
        "execution": {"executable": "fv3"},
        "lateral_boundary_conditions": {"interval_hours": 1, "offset": 0, "path": "/tmp/file"},
        "length": 3,
        "run_dir": "/tmp",
    }
    errors = validator("fv3.jsonschema", "properties", "fv3")
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


def test_fv3_schema_forecast_diag_table(fcstprop):
    errors = fcstprop("diag_table")
    # String value is ok:
    assert not errors("/path/to/file")
    # Anything else is not:
    assert "88 is not of type 'string'" in errors(88)


def test_fv3_schema_forecast_domain(fcstprop):
    errors = fcstprop("domain")
    # There is a fixed set of domain values:
    assert "'foo' is not one of ['global', 'regional']" in errors("foo")


def test_fv3_schema_forecast_execution(fcstprop):
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


@pytest.mark.skip("PM FIXTHIS")
def test_fv3_schema_forecast_execution_batchargs(fcstprop):
    errors = fcstprop("execution", "properties", "batchargs")
    batchargs = {
        "cores": 1,
        "debug": True,
        "exclusive": True,
        "export": "string",
        "jobname": "string",
        "memory": "string",
        "nodes": 1,
        "partition": "string",
        "placement": "string",
        "queue": "string",
        "rundir": "string",
        "shell": "string",
        "stdout": "string",
        "tasks_per_node": 1,
        "threads": 1,
        "walltime": "string",
    }
    # Basic correctness:
    assert not errors({"queue": "string", "walltime": "string"})
    # Full suite of accepted entries:
    assert not errors(batchargs)
    # Additional entries are not allowed:
    assert "Additional properties are not allowed" in errors({**batchargs, "foo": "bar"})


def test_fv3_schema_forecast_execution_executable(fcstprop):
    errors = fcstprop("execution", "properties", "executable")
    # String value is ok:
    assert not errors("fv3.exe")
    # Anything else is not:
    assert "88 is not of type 'string'" in errors(88)


def test_fv3_schema_forecast_execution_mpiargs(fcstprop):
    errors = fcstprop("execution", "properties", "mpiargs")
    # Basic correctness:
    assert not errors(["string1", "string2"])
    # mpiargs may be empty:
    assert not errors([])
    # String values are expected:
    assert "88 is not of type 'string'" in errors(["string1", 88])


def test_fv3_schema_forecast_execution_threads(fcstprop):
    errors = fcstprop("execution", "properties", "threads")
    # threads must be non-negative, and an integer:
    assert not errors(0)
    assert not errors(4)
    assert "-1 is less than the minimum of 0" in errors(-1)
    assert "3.14 is not of type 'integer'" in errors(3.14)


def test_fv3_schema_forecast_field_table(fcstprop, field_table_vals):
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


def test_fv3_schema_forecast_field_table_update_values(fcstprop, field_table_vals):
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


def test_fv3_schema_forecast_files_to_copy():
    test_fv3_schema_filesToStage()


def test_fv3_schema_forecast_files_to_link():
    test_fv3_schema_filesToStage()


def test_fv3_schema_forecast_lateral_boundary_conditions(fcstprop):
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


def test_fv3_schema_forecast_length(fcstprop):
    errors = fcstprop("length")
    # Positive int is ok:
    assert not errors(6)
    # Zero is not ok:
    assert "0 is less than the minimum of 1" in errors(0)
    # A negative number is not ok:
    assert "-1 is less than the minimum of 1" in errors(-1)
    # Something other than an int is not ok:
    assert "'a string' is not of type 'integer'" in errors("a string")


def test_fv3_schema_forecast_model_configure(fcstprop):
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


def test_fv3_schema_forecast_model_configure_update_values(fcstprop):
    errors = fcstprop("model_configure", "properties", "update_values")
    # boolean, number, and string values are ok:
    assert not errors({"bool": True, "int": 88, "float": 3.14, "string": "foo"})
    # Other types are not, e.g.:
    assert "None is not of type 'boolean', 'number', 'string'" in errors({"null": None})
    # At least one entry is required:
    assert "does not have enough properties" in errors({})


def test_fv3_schema_forecast_namelist(fcstprop):
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


def test_fv3_schema_forecast_namelist_update_values(fcstprop):
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


def test_fv3_schema_forecast_run_dir(fcstprop):
    errors = fcstprop("run_dir")
    # Must be a string:
    assert not errors("/some/path")
    assert "88 is not of type 'string'" in errors(88)


# @fixture
# def create_field_table_update_obj():
#     return YAMLConfig(fixture_path("FV3_GFS_v16_update.yaml"))

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
#     config_file = fixture_path("fv3.yaml")
#     with patch.object(Driver, "_validate", return_value=True):
#         forecast = FV3(config_file=config_file)
#     assert forecast.batch_script().content() == expected


# def test_create_model_configure(cycle, tmp_path):
#     """
#     Test that providing a YAML base input file and a config file will create and update YAML
#     config file.
#     """
#     config_file = fixture_path("fruit_config_similar_for_fcst.yaml")
#     base_file = fixture_path("fruit_config.yaml")
#     fcst_config_file = tmp_path / "fcst.yml"
#     fcst_config = YAMLConfig(config_file)
#     fcst_config["fv3"]["model_configure"]["base_file"] = base_file
#     fcst_config.dump(fcst_config_file)
#     output_file = (tmp_path / "test_config_from_yaml.yaml").as_posix()
#     with patch.object(FV3, "_validate", return_value=True):
#         forecast_obj = FV3(config_file=fcst_config_file, cycle=cycle)
#     forecast_obj.create_model_configure(output_file)
#     expected = YAMLConfig(base_file)
# expected.update_values(YAMLConfig(config_file)["fv3"]["model_configure"]["update_values"])
#     expected_file = tmp_path / "expected_yaml.yaml"
#     expected.dump(expected_file)
#     assert compare_files(expected_file, output_file)


# def test_create_field_table_with_base_file(create_field_table_update_obj, cycle, tmp_path):
#     """
#     Tests create_field_table method with optional base file.
#     """
#     base_file = fixture_path("FV3_GFS_v16.yaml")
#     outfldtbl_file = tmp_path / "field_table_two.FV3_GFS"
#     expected = fixture_path("field_table_from_base.FV3_GFS")
#     config_file = tmp_path / "fcst.yaml"
#     forecast_config = create_field_table_update_obj
#     forecast_config["fv3"]["field_table"]["base_file"] = base_file
#     forecast_config.dump(config_file)
#     Fv3(config_file=config_file, cycle=cycle).create_field_table(outfldtbl_file)
#     assert compare_files(expected, outfldtbl_file)


# def test_create_field_table_without_base_file(cycle, tmp_path):
#     """
#     Tests create_field_table without optional base file.
#     """
#     outfldtbl_file = tmp_path / "field_table_one.FV3_GFS"
#     expected = fixture_path("field_table_from_input.FV3_GFS")
#     config_file = fixture_path("FV3_GFS_v16_update.yaml")
#     Fv3(config_file=config_file, cycle=cycle).create_field_table(outfldtbl_file)
#     assert compare_files(expected, outfldtbl_file)


# def test_create_model_configure_call_private(cycle, tmp_path):
#     basefile = str(tmp_path / "base.yaml")
#     infile = fixture_path("fv3.yaml")
#     outfile = str(tmp_path / "out.yaml")
#     for path in infile, basefile:
#         Path(path).touch()
#     with patch.object(Driver, "_create_user_updated_config") as _create_user_updated_config:
#         with patch.object(Fv3, "_validate", return_value=True):
#             Fv3(config_file=infile, cycle=cycle).create_model_configure(outfile)
#     _create_user_updated_config.assert_called_with(
#         config_class=YAMLConfig, config_values={}, output_path=outfile
#     )


# @fixture
# def create_namelist_assets(tmp_path):
#     update_values = {
#         "salad": {
#             "base": "kale",
#             "fruit": "banana",
#             "vegetable": "tomato",
#             "how_many": 12,
#             "dressing": "balsamic",
#         }
#     }
#     return update_values, tmp_path / "create_out.nml"


# def test_create_namelist_with_base_file(create_namelist_assets, cycle, tmp_path):
#     """
#     Tests create_namelist method with optional base file.
#     """
#     update_values, outnml_file = create_namelist_assets
#     base_file = fixture_path("simple3.nml")
#     fcst_config = {
#         "fv3": {
#             "namelist": {
#                 "base_file": base_file,
#                 "update_values": update_values,
#             },
#         },
#     }
#     fcst_config_file = tmp_path / "fcst.yml"
#     YAMLConfig.dump_dict(cfg=fcst_config, path=fcst_config_file)
#     FV3(config_file=fcst_config_file, cycle=cycle).create_namelist(outnml_file)
#     expected = """
# &salad
#     base = 'kale'
#     fruit = 'banana'
#     vegetable = 'tomato'
#     how_many = 12
#     dressing = 'balsamic'
#     toppings = ,
#     extras = 0
#     dessert = .false.
#     appetizer = ,
# /
# """.lstrip()
#     with open(outnml_file, "r", encoding="utf-8") as out_file:
#         assert out_file.read() == expected


# def test_create_namelist_without_base_file(create_namelist_assets, cycle, tmp_path):
#     """
#     Tests create_namelist method without optional base file.
#     """
#     update_values, outnml_file = create_namelist_assets
#     fcst_config = {
#         "fv3": {
#             "namelist": {
#                 "update_values": update_values,
#             },
#         },
#     }
#     fcst_config_file = tmp_path / "fcst.yml"
#     YAMLConfig.dump_dict(cfg=fcst_config, path=fcst_config_file)
#     FV3(config_file=fcst_config_file, cycle=cycle).create_namelist(outnml_file)
#     expected = """
# &salad
#     base = 'kale'
#     fruit = 'banana'
#     vegetable = 'tomato'
#     how_many = 12
#     dressing = 'balsamic'
# /
# """.lstrip()
#     with open(outnml_file, "r", encoding="utf-8") as out_file:
#         assert out_file.read() == expected


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


# @pytest.mark.parametrize("batch", [True, False])
# def test_FV3_run_dry_run(batch, caplog, cycle, fv3_mpi_assets, fv3_run_assets):
#     log.setLevel(logging.INFO)
#     config_file, config = fv3_run_assets
#     if batch:
#         batch_components = [
#             "#!/bin/bash",
#             "#SBATCH --account=user_account",
#             "#SBATCH --nodes=1",
#             "#SBATCH --ntasks-per-node=1",
#             "#SBATCH --qos=batch",
#             "#SBATCH --time=00:01:00",
#         ] + fv3_mpi_assets
#         expected_lines = batch_components
#     else:
#         expected_lines = [" ".join(fv3_mpi_assets)]
#     with patch.object(FV3, "_validate", return_value=True):
#         fcstobj = FV3(config_file=config_file, cycle=cycle, dry_run=True, batch=batch)
#         with patch.object(fcstobj, "_config", config):
#             fcstobj.run()
#     for line in expected_lines:
#         assert logged(caplog, line)


# @pytest.mark.parametrize(
#     "batch,method", [(True, "_run_via_batch_submission"), (False, "_run_via_local_execution")]
# )
# def test_FV3_run(batch, cycle, fv3_run_assets, method):
#     config_file, _ = fv3_run_assets
#     fcstobj = FV3(config_file=config_file, cycle=cycle, batch=batch)
#     with patch.object(fcstobj, method) as helper:
#         helper.return_value = (True, None)
#         assert fcstobj.run() is True
#         helper.assert_called_once_with()


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


# @fixture
# def fv3_run_assets(tmp_path):
#     config_file = fixture_path("fv3.yaml")
#     config = YAMLConfig(config_file)
#     config["fv3"]["run_dir"] = tmp_path.as_posix()
#     config["fv3"]["cycle_dependent"] = {"foo-file": str(tmp_path / "foo")}
#     config["fv3"]["static"] = {"static-foo-file": str(tmp_path / "foo")}
#     return config_file, config.data["fv3"]


# @fixture
# def fv3_mpi_assets():
#     return [
#         "KMP_AFFINITY=scatter",
#         "OMP_NUM_THREADS=1",
#         "OMP_STACKSIZE=512m",
#         "MPI_TYPE_DEPTH=20",
#         "ESMF_RUNTIME_COMPLIANCECHECK=OFF:depth=4",
#         "srun --export=NONE test_exec.py",
#     ]
