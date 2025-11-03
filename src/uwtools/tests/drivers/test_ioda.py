"""
IODA driver tests.
"""

from unittest.mock import patch

from pytest import fixture, raises

from uwtools.drivers.ioda import IODA
from uwtools.exceptions import UWNotImplementedError

# Fixtures


@fixture
def config(tmp_path):
    base_file = tmp_path / "base.yaml"
    base_file.write_text("foo: bar")
    return {
        "ioda": {
            "execution": {
                "batchargs": {
                    "export": "NONE",
                    "cores": 1,
                    "stdout": "/path/to/file",
                    "walltime": "00:02:00",
                },
                "envcmds": [
                    "module load some-module",
                    "module load jedi-module",
                ],
                "executable": "/path/to/bufr2ioda.x",
            },
            "configuration_file": {
                "base_file": str(base_file),
                "update_values": {"baz": "qux"},
            },
            "files_to_copy": {
                "foo": "/path/to/foo",
                "bar/baz": "/path/to/baz",
            },
            "files_to_link": {
                "foo": "/path/to/foo",
                "bar/baz": "/path/to/baz",
            },
            "rundir": str(tmp_path),
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }


@fixture
def cycle(utc):
    return utc(2024, 5, 1, 6)


@fixture
def driverobj(config, cycle):
    return IODA(config=config, cycle=cycle, batch=True)


# Tests


def test_IODA_driver_name(driverobj):
    assert driverobj.driver_name() == IODA.driver_name() == "ioda"


def test_IODA_output(driverobj):
    with raises(UWNotImplementedError) as e:
        assert driverobj.output
    assert str(e.value) == "The output() method is not yet implemented for this driver"


def test_IODA_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        configuration_file=ready_task,
        files_copied=ready_task,
        files_hardlinked=ready_task,
        files_linked=ready_task,
        runscript=ready_task,
    ):
        assert driverobj.provisioned_rundir().ready


def test_IODA_taskname(driverobj):
    assert driverobj.taskname("foo") == "20240501 06Z ioda foo"


def test_IODA__config_fn(driverobj):
    assert driverobj._config_fn == "ioda.yaml"


def test_IODA__runcmd(driverobj):
    config = str(driverobj.rundir / driverobj._config_fn)
    assert driverobj._runcmd == f"/path/to/bufr2ioda.x {config}"
