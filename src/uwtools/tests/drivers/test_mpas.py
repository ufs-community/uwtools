# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
MPAS driver tests.
"""
import datetime as dt
import logging
from pathlib import Path
from unittest.mock import patch

import f90nml  # type: ignore
import iotaa
import yaml
from lxml import etree
from pytest import fixture, mark, raises

from uwtools.drivers.mpas import MPAS
from uwtools.drivers.mpas_base import MPASBase
from uwtools.exceptions import UWNotImplementedError
from uwtools.logging import log
from uwtools.tests.support import fixture_path, logged, regex_logged

# Helpers


def streams_file(config, driverobj, drivername):
    array_elements = {"file", "stream", "var", "var_array", "var_struct"}
    array_elements_tested = set()
    driverobj.streams_file()
    path = Path(driverobj.config["rundir"], driverobj._streams_fn)
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


# Fixtures


@fixture
def config(tmp_path):
    return {
        "mpas": {
            "domain": "regional",
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
            "rundir": str(tmp_path),
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
def cycle():
    return dt.datetime(2024, 3, 22, 6)


@fixture
def driverobj(config, cycle):
    return MPAS(config=config, cycle=cycle, batch=True)


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
        "streams_file",
        "taskname",
    ],
)
def test_MPAS(method):
    assert getattr(MPAS, method) is getattr(MPASBase, method)


def test_MPAS_boundary_files(driverobj, cycle):
    ns = (0, 1)
    links = [
        driverobj.rundir / f"lbc.{(cycle+dt.timedelta(hours=n)).strftime('%Y-%m-%d_%H.%M.%S')}.nc"
        for n in ns
    ]
    assert not any(link.is_file() for link in links)
    infile_path = Path(driverobj.config["lateral_boundary_conditions"]["path"])
    infile_path.mkdir()
    for n in ns:
        path = infile_path / f"lbc.{(cycle+dt.timedelta(hours=n)).strftime('%Y-%m-%d_%H.%M.%S')}.nc"
        path.touch()
    driverobj.boundary_files()
    assert all(link.is_symlink() for link in links)


def test_MPAS_driver_name(driverobj):
    assert driverobj.driver_name() == MPAS.driver_name() == "mpas"


@mark.parametrize(
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
    driverobj = MPAS(config=path, cycle=cycle, batch=True)
    atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    for src in (atm_src, sfc_src):
        src.touch()
    getattr(driverobj, task)()
    assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


def test_MPAS_namelist_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    dst = driverobj.rundir / "namelist.atmosphere"
    assert not dst.is_file()
    path = Path(iotaa.refs(driverobj.namelist_file()))
    assert dst.is_file()
    assert logged(caplog, f"Wrote config to {path}")
    nml = f90nml.read(dst)
    assert isinstance(nml, f90nml.Namelist)


def test_MPAS_namelist_file_fails_validation(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    driverobj._config["namelist"]["update_values"]["nhyd_model"]["foo"] = None
    path = Path(iotaa.refs(driverobj.namelist_file()))
    assert not path.exists()
    assert logged(caplog, f"Failed to validate {path}")
    assert logged(caplog, "  None is not of type 'array', 'boolean', 'number', 'string'")


@mark.parametrize(("hours", "expected"), [(0.25, "00:15:00"), (120, "005_00:00:00")])
def test_MPAS_namelist_file_durations(caplog, config, cycle, hours, expected):
    log.setLevel(logging.DEBUG)
    config["mpas"]["length"] = hours
    driverobj = MPAS(config=config, cycle=cycle)
    dst = driverobj.rundir / "namelist.atmosphere"
    assert not dst.is_file()
    path = Path(iotaa.refs(driverobj.namelist_file()))
    assert dst.is_file()
    assert logged(caplog, f"Wrote config to {path}")
    nml = f90nml.read(dst)
    assert isinstance(nml, f90nml.Namelist)
    assert nml["nhyd_model"]["config_run_duration"] == expected


def test_MPAS_namelist_file_missing_base_file(caplog, driverobj):
    log.setLevel(logging.DEBUG)
    base_file = str(Path(driverobj.config["rundir"], "missing.nml"))
    driverobj._config["namelist"]["base_file"] = base_file
    path = Path(iotaa.refs(driverobj.namelist_file()))
    assert not path.exists()
    assert regex_logged(caplog, "missing.nml: Not ready [external asset]")


def test_MPAS_output(driverobj):
    with raises(UWNotImplementedError) as e:
        assert driverobj.output
    assert str(e.value) == "The output() method is not yet implemented for this driver"


@mark.parametrize("domain", ("global", "regional"))
def test_MPAS_provisioned_rundir(domain, driverobj, ready_task):
    driverobj._config["domain"] = domain
    with patch.multiple(
        driverobj,
        boundary_files=ready_task,
        files_copied=ready_task,
        files_linked=ready_task,
        namelist_file=ready_task,
        runscript=ready_task,
        streams_file=ready_task,
    ) as mocks:
        driverobj.provisioned_rundir()
    excluded = ["boundary_files"] if domain == "global" else []
    for m in mocks:
        if m in excluded:
            mocks[m].assert_not_called()
        else:
            mocks[m].assert_called_once_with()


def test_MPAS_streams_file(config, driverobj):
    streams_file(config, driverobj, "mpas")


def test_MPAS__streams_fn(driverobj):
    assert driverobj._streams_fn == "streams.atmosphere"
