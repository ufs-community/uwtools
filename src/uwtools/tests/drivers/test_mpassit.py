"""
MPASSIT driver tests.
"""

from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import f90nml  # type: ignore[import-untyped]
import yaml
from pytest import fixture, mark

from uwtools.drivers import mpassit
from uwtools.drivers.mpassit import MPASSIT
from uwtools.tests.test_schemas import MPASSIT_CONFIG

# Fixtures


@fixture
def config(tmp_path):
    outfile = "MPAS-A_out.{{ (cycle + leadtime).strftime('%Y-%m-%d_%H:%M:%S') }}.nc"
    mpassit_config: dict = {"mpassit": deepcopy(MPASSIT_CONFIG)}
    mpassit_config["mpassit"]["rundir"] = str(tmp_path)
    mpassit_config["mpassit"]["namelist"]["update_values"]["config"]["output_file"] = outfile
    return mpassit_config


@fixture
def driverobj(config, cycle, leadtime):
    return MPASSIT(config=config, cycle=cycle, leadtime=leadtime, batch=True)


# Tests


def test_MPASSIT_driver_name(driverobj):
    assert driverobj.driver_name() == MPASSIT.driver_name() == "mpassit"


@mark.parametrize(
    ("key", "task", "test"),
    [("files_to_copy", "files_copied", "is_file"), ("files_to_link", "files_linked", "is_symlink")],
)
def test_MPASSIT_files_copied_and_linked(config, cycle, key, leadtime, task, test, tmp_path):
    atm, sfc = "gfs.t%sz.atmanl.nc", "gfs.t%sz.sfcanl.nc"
    atm_cfg_dst, sfc_cfg_dst = [x % "{{ cycle.strftime('%H') }}" for x in [atm, sfc]]
    atm_cfg_src, sfc_cfg_src = [str(tmp_path / (x + ".in")) for x in [atm_cfg_dst, sfc_cfg_dst]]
    config["mpassit"].update({key: {atm_cfg_dst: atm_cfg_src, sfc_cfg_dst: sfc_cfg_src}})
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(config))
    driverobj = MPASSIT(config=path, cycle=cycle, leadtime=leadtime, batch=True)
    atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    for src in (atm_src, sfc_src):
        src.touch()
    getattr(driverobj, task)()
    assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


def test_MPASSIT_namelist_file(driverobj, logged, ready_task):
    dst = driverobj._input_config_path
    assert not dst.is_file()
    with patch.object(mpassit, "file", new=ready_task):
        path = Path(driverobj.namelist_file().ref)
    assert dst.is_file()
    assert logged(f"Wrote config to {path}")
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_MPASSIT_namelist_file_fails_validation(driverobj, logged, ready_task):
    driverobj._config["namelist"]["update_values"]["config"]["nx"] = "string"
    with patch.object(mpassit, "file", new=ready_task):
        path = Path(driverobj.namelist_file().ref)
    assert not path.exists()
    assert logged(f"Failed to validate {path}")
    assert logged("  'string' is not of type 'integer'")


def test_MPASSIT_output(driverobj, tmp_path):
    assert driverobj.output == {"path": tmp_path / "MPAS-A_out.2024-05-07_12:00:00.nc"}


def test_MPASSIT_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        namelist_file=ready_task,
        files_copied=ready_task,
        files_hardlinked=ready_task,
        files_linked=ready_task,
        runscript=ready_task,
    ):
        assert driverobj.provisioned_rundir().ready


def test_MPASSIT__input_config_path(driverobj, tmp_path):
    assert driverobj._input_config_path == tmp_path / "mpassit.nml"


def test_MPASSIT__runcmd(driverobj):
    assert driverobj._runcmd == "srun /path/to/mpassit mpassit.nml"
