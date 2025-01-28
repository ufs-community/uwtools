# pylint: disable=missing-function-docstring,redefined-outer-name
"""
filter_topo driver tests.
"""
from pathlib import Path
from unittest.mock import patch

import f90nml  # type: ignore
import iotaa
from pytest import fixture, mark, raises

from uwtools.config.support import from_od
from uwtools.drivers.driver import Driver
from uwtools.drivers.filter_topo import FilterTopo
from uwtools.exceptions import UWNotImplementedError

# Fixtures


@fixture
def config(tmp_path):
    input_grid_file = tmp_path / "C403_grid.tile7.halo4.nc"
    input_grid_file.touch()
    orog_output = tmp_path / "out.oro.nc"
    orog_output.touch()
    return {
        "filter_topo": {
            "config": {
                "filtered_orog": "C403_filtered_orog.tile7.nc",
                "input_grid_file": str(input_grid_file),
                "input_raw_orog": str(orog_output),
            },
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
            "rundir": str(tmp_path / "run"),
        }
    }


@fixture
def driverobj(config):
    return FilterTopo(config=config, batch=True)


# Tests


@mark.parametrize(
    "method",
    [
        "_run_resources",
        "_run_via_batch_submission",
        "_run_via_local_execution",
        "_runcmd",
        "_runscript",
        "_runscript_done_file",
        "_runscript_path",
        "_scheduler",
        "_validate",
        "_write_runscript",
        "output",
        "run",
        "runscript",
        "taskname",
    ],
)
def test_FilterTopo(method):
    assert getattr(FilterTopo, method) is getattr(Driver, method)


def test_FilterTopo_driver_name(driverobj):
    assert driverobj.driver_name() == FilterTopo.driver_name() == "filter_topo"


def test_FilterTopo_filtered_output_file(driverobj):
    path = Path(driverobj.config["rundir"], "C403_filtered_orog.tile7.nc")
    assert not path.is_file()
    driverobj.filtered_output_file()
    assert path.is_file()


def test_FilterTopo_input_grid_file(driverobj):
    path = Path(driverobj.config["rundir"], "C403_grid.tile7.halo4.nc")
    assert not path.is_file()
    driverobj.input_grid_file()
    assert path.is_symlink()


def test_FilterTopo_namelist_file(driverobj):
    path = iotaa.refs(driverobj.namelist_file())
    actual = from_od(f90nml.read(path).todict())
    expected = driverobj.config["namelist"]["update_values"]
    assert actual == expected


def test_FilterTopo_output(driverobj):
    with raises(UWNotImplementedError) as e:
        assert driverobj.output
    assert str(e.value) == "The output() method is not yet implemented for this driver"


def test_FilterTopo_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        input_grid_file=ready_task,
        filtered_output_file=ready_task,
        namelist_file=ready_task,
        runscript=ready_task,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()
