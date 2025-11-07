"""
GSI driver tests.
"""

from pathlib import Path
from textwrap import dedent
from unittest.mock import DEFAULT, patch

import f90nml  # type: ignore[import-untyped]
import yaml
from pytest import fixture, mark

from uwtools.drivers.gsi import GSI
from uwtools.tests.support import fixture_path

# Fixtures


@fixture
def config(tmp_path):
    return {
        "gsi": {
            "execution": {
                "executable": "/path/to/gsi.x",
                "batchargs": {
                    "walltime": "01:30:00",
                },
            },
            "coupler.res": {
                "template_file": "/path/to/template.txt",
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
            "obs_input_file": str(tmp_path / "obs_input.txt"),
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
    return GSI(config=config, cycle=cycle, batch=True)


# Tests


def test_GSI_coupler_res(driverobj):
    src = driverobj.rundir / "coupler.res.in"
    src.touch()
    driverobj._config["coupler.res"] = {"template_file": src}
    dst = driverobj.rundir / "coupler.res"
    assert not dst.is_file()
    driverobj.coupler_res()
    assert dst.is_file()


def test_GSI_driver_name(driverobj):
    assert driverobj.driver_name() == GSI.driver_name() == "gsi"


def test_GSI_filelist(driverobj):
    driverobj._config["filelist"] = {"foo", "bar", "baz"}
    filelist = driverobj.rundir / "filelist03"
    assert not filelist.is_file()
    driverobj.filelist()
    assert filelist.is_file()
    expected_content = """
    bar
    baz
    foo
    """
    assert filelist.read_text() == dedent(expected_content).strip()


@mark.parametrize(
    ("key", "task", "test"),
    [("files_to_copy", "files_copied", "is_file"), ("files_to_link", "files_linked", "is_symlink")],
)
def test_GSI_files_copied_and_files_linked(config, cycle, key, task, test, tmp_path):
    atm, sfc = "gfs.t%sz.atmanl.nc", "gfs.t%sz.sfcanl.nc"
    atm_cfg_dst, sfc_cfg_dst = [x % "{{ cycle.strftime('%H') }}" for x in [atm, sfc]]
    atm_cfg_src, sfc_cfg_src = [str(tmp_path / (x + ".in")) for x in [atm_cfg_dst, sfc_cfg_dst]]
    config["gsi"].update({key: {atm_cfg_dst: atm_cfg_src, sfc_cfg_dst: sfc_cfg_src}})
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(config))
    driverobj = GSI(config=path, cycle=cycle, batch=True)
    atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    for src in (atm_src, sfc_src):
        src.touch()
    getattr(driverobj, task)()
    assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


def test_GSI_namelist_file(driverobj, logged):
    obs_input = driverobj.rundir / "obs_input.txt"
    obs_input.write_text("OBS_INPUT GOES HERE")
    dst = driverobj.rundir / "gsiparm.anl"
    assert not dst.is_file()
    path = Path(driverobj.namelist_file().ref)
    assert path == dst
    assert dst.is_file()
    assert logged(f"Wrote config to {path}")
    nml = f90nml.read(dst)
    assert isinstance(nml, f90nml.Namelist)
    assert nml["a"]["start"] == 1
    content = dst.read_text().split("\n")
    assert content[-1] == "OBS_INPUT GOES HERE"


def test_GSI_namelist_file__fail(caplog, driverobj):
    driverobj._config["namelist"] = {}
    node = driverobj.namelist_file()
    assert not node.ready
    assert not node.ref.is_file()
    # Different versions of jsonschema emit different error messages for the same issue:
    assert any(x in caplog.text for x in ["should be non-empty", "does not have enough properties"])


def test_GSI_runscript(driverobj):
    dst = driverobj.rundir / "runscript.gsi"
    assert not dst.is_file()
    driverobj.runscript()
    assert dst.is_file()
    content = dst.read_text()
    assert driverobj._runcmd in content


def test_GSI_namelist_file__missing_base_file(driverobj, logged):
    base_file = str(Path(driverobj.config["rundir"], "missing.nml"))
    driverobj._config["namelist"]["base_file"] = base_file
    path = Path(driverobj.namelist_file().ref)
    assert not path.exists()
    assert logged("missing.nml: Not ready [external asset]")


@mark.parametrize("filelist", [[], ["a", "b"]])
def test_GSI_provisioned_rundir(driverobj, filelist, ready_task):
    if filelist:
        driverobj._config["filelist"] = filelist
    with patch.multiple(
        driverobj,
        coupler_res=ready_task,
        filelist=ready_task if filelist else DEFAULT,
        files_copied=ready_task,
        files_hardlinked=ready_task,
        files_linked=ready_task,
        namelist_file=ready_task,
        runscript=ready_task,
    ):
        assert driverobj.provisioned_rundir().ready


def test_GSI__input_config_path(driverobj):
    assert driverobj._input_config_path == driverobj.rundir / "gsiparm.anl"


def test_GSI__runcmd(driverobj):
    expected = [
        "/path/to/gsi.x",
        "<",
        str(driverobj.rundir / "gsiparm.anl"),
    ]
    assert driverobj._runcmd == " ".join(expected)
