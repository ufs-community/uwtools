# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
filter_topo driver tests.
"""
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
from iotaa import refs
from pytest import fixture

from uwtools.config.support import from_od
from uwtools.drivers.driver import Driver
from uwtools.drivers.filter_topo import FilterTopo

# Fixtures


@fixture
def config(tmp_path):
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
            "run_dir": str(tmp_path),
        }
    }


@fixture
def driverobj(config):
    return FilterTopo(config=config, batch=True)


# Tests


def test_FilterTopo():
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


def test_FilterTopo_namelist_file(driverobj):
    path = refs(driverobj.namelist_file())
    actual = from_od(f90nml.read(path).todict())
    expected = driverobj._driver_config["namelist"]["update_values"]
    assert actual == expected


def test_FilterTopo_provisioned_run_directory(driverobj):
    with patch.multiple(driverobj, namelist_file=D, runscript=D) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_FilterTopo__taskname(driverobj):
    assert driverobj._taskname("foo") == "filter_topo foo"
