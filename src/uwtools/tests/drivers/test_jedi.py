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
from pytest import fixture

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers import jedi
from uwtools.scheduler import Slurm
from uwtools.tests.support import regex_logged

# Fixtures


@fixture
def cycle():
    return dt.datetime(2024, 2, 1, 18)


# Driver fixtures


@fixture
def config(tmp_path):
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
                "base_file": str(tmp_path / "base.yaml"),
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
def config_file(config, tmp_path):
    path = tmp_path / "base.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    return path


@fixture
def driverobj(config_file, cycle):
    return jedi.JEDI(config=config_file, cycle=cycle, batch=True)


# Driver tests


def test_JEDI(driverobj):
    assert isinstance(driverobj, jedi.JEDI)


def test_JEDI_dry_run(config_file, cycle):
    with patch.object(jedi, "dryrun") as dryrun:
        driverobj = jedi.JEDI(config=config_file, cycle=cycle, batch=True, dry_run=True)
    assert driverobj._dry_run is True
    dryrun.assert_called_once_with()


def test_JEDI_files_copied(driverobj):
    with patch.object(jedi, "filecopy") as filecopy:
        driverobj._driver_config["run_dir"] = "/path/to/run"
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
    with patch.object(jedi, "symlink") as symlink:
        driverobj._driver_config["run_dir"] = "/path/to/run"
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


def test_JEDI_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        files_copied=D,
        files_linked=D,
        runscript=D,
        configuration_file=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_JEDI_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_JEDI_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_JEDI_runscript(driverobj):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_JEDI_validate_only(caplog, driverobj):

    @external
    def file(path: Path):
        yield "Mocked file task for %s" % path
        yield asset(path, lambda: True)

    logging.getLogger().setLevel(logging.INFO)
    with patch.object(jedi, "file"):
        with patch.object(jedi, "run") as run:
            result = Mock(output="", success=True)
            run.return_value = result
            driverobj.validate_only()
            cfgfile = Path(driverobj._driver_config["run_dir"]) / "jedi.yaml"
            cmds = [
                "module load some-module",
                "module load jedi-module",
                "time /path/to/qg_forecast.x --validate-only %s 2>&1" % (cfgfile),
            ]
            run.assert_called_once_with("20240201 18Z jedi validate_only", " && ".join(cmds))
    assert regex_logged(caplog, "Config is valid")


def test_JEDI_configuration_file(driverobj):
    basecfg = {"foo": "bar"}
    basefile = Path(driverobj._driver_config["configuration_file"]["base_file"])
    with open(basefile, "w", encoding="utf-8") as f:
        yaml.dump(basecfg, f)
    cfgfile = Path(driverobj._driver_config["run_dir"]) / "jedi.yaml"
    assert not cfgfile.is_file()
    driverobj.configuration_file()
    assert cfgfile.is_file()
    newcfg = YAMLConfig(config=cfgfile)
    assert newcfg == {**basecfg, "baz": "qux"}


def test_JEDI__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.jedi"


def test_JEDI__taskname(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z jedi foo"
