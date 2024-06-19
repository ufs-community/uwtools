# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
IODA driver tests.
"""
import datetime as dt
from unittest.mock import DEFAULT as D
from unittest.mock import patch

from pytest import fixture

from uwtools.drivers.ioda import IODA
from uwtools.drivers.jedi_base import JEDIBase

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
            "run_dir": str(tmp_path),
        },
        "platform": {
            "account": "me",
            "scheduler": "slurm",
        },
    }


@fixture
def cycle():
    return dt.datetime(2024, 5, 1, 6)


@fixture
def driverobj(config, cycle):
    return IODA(config=config, cycle=cycle, batch=True)


# Tests


def test_IODA():
    for method in [
        "_driver_config",
        "_resources",
        "_run_via_batch_submission",
        "_run_via_local_execution",
        "_runscript",
        "_runscript_done_file",
        "_runscript_path",
        "_scheduler",
        "_validate",
        "_write_runscript",
        "run",
        "runscript",
    ]:
        assert getattr(IODA, method) is getattr(JEDIBase, method)


def test_IODA_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        configuration_file=D,
        files_copied=D,
        files_linked=D,
        runscript=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_IODA__config_fn(driverobj):
    assert driverobj._config_fn == "ioda.yaml"


def test_IODA__driver_name(driverobj):
    assert driverobj._driver_name == "ioda"


def test_IODA__runcmd(driverobj):
    config = str(driverobj._rundir / driverobj._config_fn)
    assert driverobj._runcmd == f"/path/to/bufr2ioda.x {config}"


def test_IODA__taskname(driverobj):
    assert driverobj._taskname("foo") == "20240501 06Z ioda foo"
