# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
JEDI driver tests.
"""
import datetime as dt
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import pytest
import yaml
from pytest import fixture

from uwtools.drivers import jedi
from uwtools.scheduler import Slurm
from uwtools.tests.support import fixture_path

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
                    "module use /scratch1/NCEPDEV/nems/role.epic/spack-stack/spack-stack-1.5.0/envs/unified-env-rocky8/install/modulefiles/Core",
                    "module load stack-intel/2021.5.0",
                    "module load stack-intel-oneapi-mpi/2021.5.1",
                    "module load jedi-fv3-env/1.0.0",
                ],
                "executable": "/scratch2/BMC/zrtrr/Naureen.Bharwani/build/bin/qg_forecast.x",
                "mpiargs": ["--export=ALL", "--ntasks $SLURM_CPUS_ON_NODE"],
                "mpicmd": "srun",
            },
            "configuration_file": {
                "base_file": str(fixture_path("jedi.yaml")),
                "update_values": {"jedi": {}},
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
    path = tmp_path / "config.yaml"
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


@pytest.mark.parametrize(
    "key,task,test",
    [("files_to_copy", "files_copied", "is_file"), ("files_to_link", "files_linked", "is_symlink")],
)
def test_JEDI_files_copied_and_linked(config, cycle, key, task, test, tmp_path):
    pass
    # atm, sfc = "gfs.t%sz.atmanl.nc", "gfs.t%sz.sfcanl.nc"
    # atm_cfg_dst, sfc_cfg_dst = [x % "{{ cycle.strftime('%H') }}" for x in [atm, sfc]]
    # atm_cfg_src, sfc_cfg_src = [str(tmp_path / (x + ".in")) for x in [atm_cfg_dst, sfc_cfg_dst]]
    # config["mpas"].update({key: {atm_cfg_dst: atm_cfg_src, sfc_cfg_dst: sfc_cfg_src}})
    # path = tmp_path / "config.yaml"
    # with open(path, "w", encoding="utf-8") as f:
    #     yaml.dump(config, f)
    # driverobj = jedi.JEDI(config=path, cycle=cycle, batch=True)
    # atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    # assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    # atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    # for src in (atm_src, sfc_src):
    #     src.touch()
    # getattr(driverobj, task)()
    # assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


def test_JEDI_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        files_copied=D,
        files_linked=D,
        runscript=D,
        yaml_file=D,
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


def test_JEDI_validate_only(config_file, cycle, driverobj):
    # with patch.object(jedi, "run")
    driverobj.validate_only()


def test_JEDI_yaml_file(driverobj):
    pass
    # src = driverobj._rundir / "input.yaml"


def test_JEDI__driver_config(driverobj):
    assert driverobj._driver_config == driverobj._config["jedi"]


def test_JEDI__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.jedi"


def test_JEDI__taskname(driverobj):
    assert driverobj._taskname("foo") == "20240201 18Z jedi foo"
