# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
JEDI driver tests.
"""
import datetime as dt
import logging
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import Mock, call, patch

import yaml
from iotaa import asset, external
from pytest import fixture, mark

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers import jedi, jedi_base
from uwtools.drivers.jedi import JEDI
from uwtools.drivers.jedi_base import JEDIBase
from uwtools.logging import log
from uwtools.tests.support import regex_logged

# Fixtures


@fixture
def config(tmp_path):
    base_file = tmp_path / "base.yaml"
    base_file.write_text("foo: bar")
    return {
        "jedi": {
            "execution": {
                "batchargs": {
                    "export": "NONE",
                    "nodes": 1,
                    "stdout": "/path/to/file",
                    "walltime": "00:02:00",
                },
                "envcmds": [
                    "module load some-module",
                    "module load jedi-module",
                ],
                "executable": "/path/to/qg_forecast.x",
                "mpiargs": ["--export=ALL", "--ntasks $SLURM_CPUS_ON_NODE"],
                "mpicmd": "srun",
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
def cycle():
    return dt.datetime(2024, 2, 1, 18)


@fixture
def driverobj(config, cycle):
    return JEDI(config=config, cycle=cycle, batch=True)


# Tests


@mark.parametrize(
    "method",
    [
        "_run_resources",
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
    ],
)
def test_JEDI(method):
    assert getattr(JEDI, method) is getattr(JEDIBase, method)


def test_JEDI_configuration_file(driverobj):
    basecfg = {"foo": "bar"}
    base_file = Path(driverobj.config["configuration_file"]["base_file"])
    with open(base_file, "w", encoding="utf-8") as f:
        yaml.dump(basecfg, f)
    cfgfile = Path(driverobj.config["rundir"], "jedi.yaml")
    assert not cfgfile.is_file()
    driverobj.configuration_file()
    assert cfgfile.is_file()
    newcfg = YAMLConfig(config=cfgfile)
    assert newcfg == {**basecfg, "baz": "qux"}


def test_JEDI_configuration_file_missing_base_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    base_file = Path(driverobj.config["rundir"], "missing")
    driverobj._config["configuration_file"]["base_file"] = base_file
    cfgfile = Path(driverobj.config["rundir"], "jedi.yaml")
    assert not cfgfile.is_file()
    driverobj.configuration_file()
    assert not cfgfile.is_file()
    assert regex_logged(caplog, f"{base_file}: State: Not Ready (external asset)")


def test_JEDI_files_copied(driverobj):
    with patch.object(jedi_base, "filecopy") as filecopy:
        driverobj._config["rundir"] = "/path/to/run"
        driverobj.files_copied()
        assert filecopy.call_count == 2
        assert (
            call(src=Path("/path/to/baz"), dst=Path("/path/to/run/bar/baz"))
            in filecopy.call_args_list
        )
        assert (
            call(src=Path("/path/to/foo"), dst=Path("/path/to/run/foo")) in filecopy.call_args_list
        )


def test_JEDI_files_linked(driverobj):
    with patch.object(jedi_base, "symlink") as symlink:
        driverobj._config["rundir"] = "/path/to/run"
        driverobj.files_linked()
        assert symlink.call_count == 2
        assert (
            call(target=Path("/path/to/baz"), linkname=Path("/path/to/run/bar/baz"))
            in symlink.call_args_list
        )
        assert (
            call(target=Path("/path/to/foo"), linkname=Path("/path/to/run/foo"))
            in symlink.call_args_list
        )


def test_JEDI_provisioned_rundir(driverobj):
    with patch.multiple(
        driverobj,
        configuration_file=D,
        files_copied=D,
        files_linked=D,
        runscript=D,
        validate_only=D,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_JEDI_validate_only(caplog, driverobj):

    @external
    def file(path: Path):
        yield "Mocked file task for %s" % path
        yield asset(path, lambda: True)

    logging.getLogger().setLevel(logging.INFO)
    with patch.object(jedi, "file", file):
        with patch.object(jedi, "run") as run:
            result = Mock(output="", success=True)
            run.return_value = result
            driverobj.validate_only()
            cfgfile = Path(driverobj.config["rundir"], "jedi.yaml")
            cmds = [
                "module load some-module",
                "module load jedi-module",
                "time %s --validate-only %s 2>&1"
                % (driverobj.config["execution"]["executable"], cfgfile),
            ]
            run.assert_called_once_with("20240201 18Z jedi validate_only", " && ".join(cmds))
    assert regex_logged(caplog, "Config is valid")


def test_JEDI__config_fn(driverobj):
    assert driverobj._config_fn == "jedi.yaml"


def test_JEDI__driver_name(driverobj):
    assert driverobj._driver_name == "jedi"


def test_JEDI__runcmd(driverobj):
    executable = driverobj.config["execution"]["executable"]
    config = driverobj.rundir / driverobj._config_fn
    assert (
        driverobj._runcmd == f"srun --export=ALL --ntasks $SLURM_CPUS_ON_NODE {executable} {config}"
    )


def test_JEDI__taskname(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z jedi foo"
