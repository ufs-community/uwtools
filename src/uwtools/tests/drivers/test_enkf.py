"""
EnKF driver tests.
"""

from pathlib import Path
from unittest.mock import call, patch

import yaml
from pytest import fixture, mark

from uwtools.api.config import get_nml_config
from uwtools.drivers import enkf
from uwtools.tests.support import fixture_path

# Fixtures


@fixture
def config(tmp_path):
    return {
        "enkf": {
            "execution": {
                "executable": "/path/to/enkf.x",
                "batchargs": {
                    "walltime": "01:30:00",
                },
            },
            "background_files": {
                "files": {"mem{{ member }}": "/path/to/mem{{ '%03d' % member }}.nc"},
                "ensemble_size": 3,
            },
            "files_to_link": {
                "file1": "/path/to/file1.txt",
                "file2": "/path/to/file2.txt",
            },
            "namelist": {
                "base_file": str(fixture_path("simple.nml")),
                "update_values": {
                    "a": {"start": 1, "stop": 2},
                },
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
    return utc(2024, 2, 1, 18)


@fixture
def driverobj(config, cycle):
    return enkf.EnKF(config=config, cycle=cycle, batch=True)


# Tests


def test_EnKF_background_files(driverobj, tmp_path):
    with patch.object(enkf, "Linker") as linker:
        driverobj.background_files()
    expected_calls = [
        call(config={"mem1": "/path/to/mem001.nc"}, target_dir=tmp_path),
        call(config={"mem2": "/path/to/mem002.nc"}, target_dir=tmp_path),
        call(config={"mem3": "/path/to/mem003.nc"}, target_dir=tmp_path),
    ]
    assert all(c in linker.call_args_list for c in expected_calls)


def test_EnKF_driver_name(driverobj):
    assert driverobj.driver_name() == enkf.EnKF.driver_name() == "enkf"


@mark.parametrize(
    ("key", "task", "test"),
    [("files_to_copy", "files_copied", "is_file"), ("files_to_link", "files_linked", "is_symlink")],
)
def test_EnKF_files_copied_and_files_linked(config, cycle, key, task, test, tmp_path):
    atm, sfc = "gfs.t%sz.atmanl.nc", "gfs.t%sz.sfcanl.nc"
    atm_cfg_dst, sfc_cfg_dst = [x % "{{ cycle.strftime('%H') }}" for x in [atm, sfc]]
    atm_cfg_src, sfc_cfg_src = [str(tmp_path / (x + ".in")) for x in [atm_cfg_dst, sfc_cfg_dst]]
    config["enkf"].update({key: {atm_cfg_dst: atm_cfg_src, sfc_cfg_dst: sfc_cfg_src}})
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(config))
    driverobj = enkf.EnKF(config=path, cycle=cycle, batch=True)
    atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    for src in (atm_src, sfc_src):
        src.touch()
    getattr(driverobj, task)()
    assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


def test_EnKF_namelist_file(driverobj):
    dst = driverobj.rundir / "enkf.nml"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()
    contents = get_nml_config(dst)
    assert contents["a"]["start"] == 1
    assert contents["a"]["stop"] == 2


def test_EnKF_runscript(driverobj):
    dst = driverobj.rundir / "runscript.enkf"
    assert not dst.is_file()
    driverobj.runscript()
    assert dst.is_file()
    content = dst.read_text()
    assert driverobj._runcmd in content


def test_EnKF_namelist_file__missing_base_file(driverobj, logged):
    base_file = str(Path(driverobj.config["rundir"], "missing.nml"))
    driverobj._config["namelist"]["base_file"] = base_file
    path = Path(driverobj.namelist_file().ref)
    assert not path.exists()
    assert logged("missing.nml: Not ready [external asset]")


def test_EnKF_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        files_copied=ready_task,
        files_hardlinked=ready_task,
        files_linked=ready_task,
        namelist_file=ready_task,
        runscript=ready_task,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_EnKF__input_config_path(driverobj):
    assert driverobj._input_config_path == driverobj.rundir / "enkf.nml"


def test_EnKF__runcmd(driverobj):
    expected = [
        "/path/to/enkf.x",
        "<",
        str(driverobj.rundir / "enkf.nml"),
    ]
    assert driverobj._runcmd == " ".join(expected)
