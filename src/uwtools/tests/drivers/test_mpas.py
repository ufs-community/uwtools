# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
MPAS driver tests.
"""
import datetime as dt
import logging
from pathlib import Path
from unittest.mock import DEFAULT as D
from unittest.mock import patch

import f90nml  # type: ignore
import pytest
import yaml
from iotaa import refs
from lxml import etree
from pytest import fixture

from uwtools.drivers import mpas
from uwtools.logging import log
from uwtools.scheduler import Slurm
from uwtools.tests.support import fixture_path, logged, regex_logged

# Fixtures


@fixture
def config(tmp_path):
    return {
        "mpas": {
            "execution": {
                "executable": "atmosphere_model",
                "batchargs": {
                    "walltime": "01:30:00",
                },
            },
            "files_to_link": {
                "CAM_ABS_DATA.DBL": "src/MPAS-Model/CAM_ABS_DATA.DBL",
                "CAM_AEROPT_DATA.DBL": "src/MPAS-Model/CAM_AEROPT_DATA.DBL",
            },
            "lateral_boundary_conditions": {
                "interval_hours": 1,
                "offset": 0,
                "path": str(tmp_path / "input_files"),
            },
            "length": 1,
            "namelist": {
                "base_file": str(fixture_path("simple.nml")),
                "update_values": {
                    "nhyd_model": {"config_start_time": "12", "config_stop_time": "12"},
                },
            },
            "run_dir": str(tmp_path),
            "streams": {
                "input": {
                    "filename_template": "conus.init.nc",
                    "input_interval": "initial_only",
                    "mutable": False,
                    "type": "input",
                },
                "output": {
                    "clobber_mode": "overwrite",
                    "filename_template": "history.$Y-$M-$D_$h.$m.$s.nc",
                    "files": ["stream_list.atmosphere.output"],
                    "io_type": "pnetcdf",
                    "mutable": True,
                    "output_interval": "6:00:00",
                    "precision": "single",
                    "reference_time": "2024-06-06 00:00:00",
                    "streams": ["stream1", "stream2"],
                    "type": "output",
                    "vars": ["v1", "v2"],
                    "var_arrays": ["va1", "va2"],
                    "var_structs": ["vs1", "vs2"],
                },
            },
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
def cycle():
    return dt.datetime(2024, 3, 22, 6)


@fixture
def driverobj(config_file, cycle):
    return mpas.MPAS(config=config_file, cycle=cycle, batch=True)


# Helpers


def streams_file(config, driverobj, drivername):
    array_elements = {"file", "stream", "var", "var_array", "var_struct"}
    array_elements_tested = set()
    driverobj.streams_file()
    path = Path(driverobj._driver_config["run_dir"]) / driverobj._streams_fn
    with open(path, "r", encoding="utf-8") as f:
        xml = etree.parse(f).getroot()
    assert xml.tag == "streams"
    for child in xml.getchildren():  # type: ignore
        block = config[drivername]["streams"][child.get("name")]
        for k, v in block.items():
            if k not in [*[f"{e}s" for e in array_elements], "mutable"]:
                assert child.get(k) == v
        assert child.tag == "stream" if block["mutable"] else "immutable_stream"
        for e in array_elements:
            for name in block.get(f"{e}s", []):
                assert child.xpath(f"//{e}[@name='{name}']")
                array_elements_tested.add(e)
    assert array_elements_tested == array_elements


# Tests


def test_MPAS(driverobj):
    assert isinstance(driverobj, mpas.MPAS)


def test_MPAS_boundary_files(driverobj, cycle):
    ns = (0, 1)
    links = [
        driverobj._rundir / f"lbc.{(cycle+dt.timedelta(hours=n)).strftime('%Y-%m-%d_%H.%M.%S')}.nc"
        for n in ns
    ]
    assert not any(link.is_file() for link in links)
    infile_path = Path(driverobj._driver_config["lateral_boundary_conditions"]["path"])
    infile_path.mkdir()
    for n in ns:
        (
            infile_path / f"lbc.{(cycle+dt.timedelta(hours=n)).strftime('%Y-%m-%d_%H.%M.%S')}.nc"
        ).touch()
    driverobj.boundary_files()
    assert all(link.is_symlink() for link in links)


@pytest.mark.parametrize(
    "key,task,test",
    [("files_to_copy", "files_copied", "is_file"), ("files_to_link", "files_linked", "is_symlink")],
)
def test_MPAS_files_copied_and_linked(config, cycle, key, task, test, tmp_path):
    atm, sfc = "gfs.t%sz.atmanl.nc", "gfs.t%sz.sfcanl.nc"
    atm_cfg_dst, sfc_cfg_dst = [x % "{{ cycle.strftime('%H') }}" for x in [atm, sfc]]
    atm_cfg_src, sfc_cfg_src = [str(tmp_path / (x + ".in")) for x in [atm_cfg_dst, sfc_cfg_dst]]
    config["mpas"].update({key: {atm_cfg_dst: atm_cfg_src, sfc_cfg_dst: sfc_cfg_src}})
    path = tmp_path / "config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    driverobj = mpas.MPAS(config=path, cycle=cycle, batch=True)
    atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    for src in (atm_src, sfc_src):
        src.touch()
    getattr(driverobj, task)()
    assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


def test_MPAS_namelist_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    dst = driverobj._rundir / "namelist.atmosphere"
    assert not dst.is_file()
    path = Path(refs(driverobj.namelist_file()))
    assert dst.is_file()
    assert logged(caplog, f"Wrote config to {path}")
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_MPAS_namelist_file_fails_validation(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    driverobj._driver_config["namelist"]["update_values"]["nhyd_model"]["foo"] = None
    path = Path(refs(driverobj.namelist_file()))
    assert not path.exists()
    assert logged(caplog, f"Failed to validate {path}")
    assert logged(caplog, "  None is not of type 'array', 'boolean', 'number', 'string'")


def test_MPAS_namelist_file_missing_base_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    base_file = str(Path(driverobj._driver_config["run_dir"]) / "missing.nml")
    driverobj._driver_config["namelist"]["base_file"] = base_file
    path = Path(refs(driverobj.namelist_file()))
    assert not path.exists()
    assert regex_logged(caplog, "missing.nml: State: Not Ready (external asset)")


def test_MPAS_provisioned_run_directory(driverobj):
    with patch.multiple(
        driverobj,
        boundary_files=D,
        files_copied=D,
        files_linked=D,
        namelist_file=D,
        runscript=D,
        streams_file=D,
    ) as mocks:
        driverobj.provisioned_run_directory()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_MPAS_run_batch(driverobj):
    with patch.object(driverobj, "_run_via_batch_submission") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_MPAS_run_local(driverobj):
    driverobj._batch = False
    with patch.object(driverobj, "_run_via_local_execution") as func:
        driverobj.run()
    func.assert_called_once_with()


def test_MPAS_runscript(driverobj):
    with patch.object(driverobj, "_runscript") as runscript:
        driverobj.runscript()
        runscript.assert_called_once()
        args = ("envcmds", "envvars", "execution", "scheduler")
        types = [list, dict, list, Slurm]
        assert [type(runscript.call_args.kwargs[x]) for x in args] == types


def test_MPAS_streams_file(config, driverobj):
    streams_file(config, driverobj, "mpas")


def test_MPAS__runscript_path(driverobj):
    assert driverobj._runscript_path == driverobj._rundir / "runscript.mpas"


def test_MPAS__taskname(driverobj):
    assert driverobj._taskname("foo") == "20240322 06Z mpas foo"


def test_MPAS__validate(driverobj):
    driverobj._validate()
