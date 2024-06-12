# pylint: disable=missing-function-docstring,redefined-outer-name
"""
orog_gsl driver tests.
"""
# from unittest.mock import DEFAULT as D
# from unittest.mock import patch

# import yaml
from pytest import fixture

from uwtools.drivers import orog_gsl

# from uwtools.scheduler import Slurm

# Driver fixtures


@fixture
def config(tmp_path):
    afile = tmp_path / "afile"
    afile.touch()
    return {
        "config": {
            "halo": 4,
            "input_grid_file": str(afile),
            "resolution": 304,
            "tile": 7,
            "topo_data_2p5m": str(afile),
            "topo_data_30s": str(afile),
        },
        "execution": {
            "executable": "/path/to/orog_gsl",
        },
        "run_dir": tmp_path,
    }


@fixture
def driverobj(config):
    return orog_gsl.OrogGSL(config=config, batch=True)


# Driver tests


def test_OrogGSL(driverobj):
    assert isinstance(driverobj, orog_gsl.OrogGSL)


# def test_OrogGSL_provisioned_run_directory(driverobj):
#     with patch.multiple(
#         driverobj,
#         runscript=D,
#     ) as mocks:
#         driverobj.provisioned_run_directory()
#     for m in mocks:
#         mocks[m].assert_called_once_with()


# def test_OrogGSL_run_batch(driverobj):
#     with patch.object(driverobj, "_run_via_batch_submission") as func:
#         driverobj.run()
#     func.assert_called_once_with()


# def test_OrogGSL_run_local(driverobj):
#     driverobj._batch = False
#     with patch.object(driverobj, "_run_via_local_execution") as func:
#         driverobj.run()
#     func.assert_called_once_with()


# def test_OrogGSL__runcmd(driverobj):
#     cmd = driverobj._runcmd
#     nx = driverobj._driver_config["config"]["nx"]
#     ny = driverobj._driver_config["config"]["ny"]
#     nh4 = driverobj._driver_config["config"]["nh4"]
#     input_file_path = driverobj._driver_config["config"]["input_grid_file"]
#     output_file_path = input_file_path.replace(".nc", "_NH0.nc")
#     assert cmd == f"/path/to/orog_gsl {nx} {ny} {nh4} {input_file_path} {output_file_path}"


# def test_OrogGSL_runscript(driverobj):
#     with patch.object(driverobj, "_runscript") as runscript:
#         driverobj.runscript()
#         runscript.assert_called_once()
#         args = ("envcmds", "envvars", "execution", "scheduler")
#         types = [list, dict, list, Slurm]
#         assert [type(runscript.call_args.kwargs[x]) for x in args] == types


# def test_OrogGSL__driver_config(driverobj):
#     assert driverobj._driver_config == driverobj._config["orog_gsl"]


# def test_OrogGSL__runscript_path(driverobj):
#     assert driverobj._runscript_path == driverobj._rundir / "runscript.orog_gsl"


# def test_OrogGSL__taskname(driverobj):
#     assert driverobj._taskname("foo") == "orog_gsl foo"


# def test_OrogGSL__validate(driverobj):
#     driverobj._validate()
