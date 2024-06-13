# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
filter_topo driver tests.
"""
# from pathlib import Path
# from unittest.mock import DEFAULT as D
# from unittest.mock import patch

from pytest import fixture

from uwtools.drivers.driver import Driver
from uwtools.drivers.filter_topo import FilterTopo

# from uwtools.scheduler import Slurm

# Fixtures


@fixture
def config():
    return {
        "filter_topo": {
            "execution": {
                "executable": "/path/to/orog_gsl",
            },
            "namelist": {
                "update_values": {
                    "filter_topo_nml": {
                        "grid_file": "/path/to/grid/file",
                        "grid_type": 0,
                        "mask_field": "land_frac",
                        "regional": True,
                        "res": 403,
                        "stretch_fac": 0.999,
                        "topo_field": "orog_filt",
                        "topo_file": "/path/to/topo/file",
                        "zero_ocean": True,
                    }
                }
            },
            "run_dir": "/path/to/run/dir",
        }
    }


@fixture
def driverobj(config):
    return FilterTopo(config=config, batch=True)


# Tests


def test_FilterTopo(driverobj):
    assert isinstance(driverobj, FilterTopo)


def test_FilterTopo_inheritance():
    for method in [
        "_driver_config",
        "_resources",
        "_run_via_batch_submission",
        "_run_via_local_execution",
        "_runcmd",
        "_runscript",
        "_runscript_done_file",
        "_runscript_path",
        "_scheduler",
        "_validate",
        "_write_runscript",
        "run",
    ]:
        assert getattr(FilterTopo, method) is getattr(Driver, method)


# def test_FilterTopo_provisioned_run_directory(driverobj):
#     with patch.multiple(
#         driverobj, input_grid_file=D, runscript=D, topo_data_2p5m=D, topo_data_30s=D
#     ) as mocks:
#         driverobj.provisioned_run_directory()
#     for m in mocks:
#         mocks[m].assert_called_once_with()


# def test_FilterTopo_runscript(driverobj):
#     with patch.object(driverobj, "_runscript") as runscript:
#         driverobj.runscript()
#         runscript.assert_called_once()
#         args = ("envcmds", "envvars", "execution", "scheduler")
#         types = [list, dict, list, Slurm]
#         assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_FilterTopo__taskname(driverobj):
    assert driverobj._taskname("foo") == "filter_topo foo"
