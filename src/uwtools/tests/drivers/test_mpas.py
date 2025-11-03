"""
MPAS driver tests.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import f90nml  # type: ignore[import-untyped]
import yaml
from lxml import etree
from pytest import fixture, mark

from uwtools.drivers.mpas import MPAS
from uwtools.tests.support import fixture_path

# Helpers


def streams_file(config, driverobj, drivername):
    array_elements = {"file", "stream", "var", "var_array", "var_struct"}
    array_elements_tested = set()
    driverobj.streams_file()
    path = Path(driverobj.config["rundir"], driverobj._streams_fn)
    xml = etree.fromstring(path.read_text())
    assert xml.tag == "streams"
    for child in xml.getchildren():  # type: ignore[attr-defined]
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
def cycle(utc):
    return utc(2024, 2, 1, 18)


@fixture
def driverobj(config, cycle):
    return MPAS(config=config, cycle=cycle, batch=True)


@fixture
def outpath(driverobj):
    return lambda fn: driverobj.rundir / fn


# Tests


def test_MPAS_boundary_files(driverobj, cycle):
    ns = (0, 1)
    links = [
        driverobj.rundir / f"lbc.{(cycle + timedelta(hours=n)).strftime('%Y-%m-%d_%H.%M.%S')}.nc"
        for n in ns
    ]
    assert not any(link.is_file() for link in links)
    infile_path = Path(driverobj.config["lateral_boundary_conditions"]["path"])
    infile_path.mkdir()
    for n in ns:
        path = infile_path / f"lbc.{(cycle + timedelta(hours=n)).strftime('%Y-%m-%d_%H.%M.%S')}.nc"
        path.touch()
    driverobj.boundary_files()
    assert all(link.is_symlink() for link in links)


def test_MPAS_driver_name(driverobj):
    assert driverobj.driver_name() == MPAS.driver_name() == "mpas"


@mark.parametrize(
    ("key", "task", "test"),
    [("files_to_copy", "files_copied", "is_file"), ("files_to_link", "files_linked", "is_symlink")],
)
def test_MPAS_files_copied_and_files_linked(config, cycle, key, task, test, tmp_path):
    atm, sfc = "gfs.t%sz.atmanl.nc", "gfs.t%sz.sfcanl.nc"
    atm_cfg_dst, sfc_cfg_dst = [x % "{{ cycle.strftime('%H') }}" for x in [atm, sfc]]
    atm_cfg_src, sfc_cfg_src = [str(tmp_path / (x + ".in")) for x in [atm_cfg_dst, sfc_cfg_dst]]
    config["mpas"].update({key: {atm_cfg_dst: atm_cfg_src, sfc_cfg_dst: sfc_cfg_src}})
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(config))
    driverobj = MPAS(config=path, cycle=cycle, batch=True)
    atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    for src in (atm_src, sfc_src):
        src.touch()
    getattr(driverobj, task)()
    assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


def test_MPAS_namelist_file(driverobj, logged):
    dst = driverobj.rundir / "namelist.atmosphere"
    assert not dst.is_file()
    path = Path(driverobj.namelist_file().ref)
    assert dst.is_file()
    assert logged(f"Wrote config to {path}")
    nml = f90nml.read(dst)
    assert isinstance(nml, f90nml.Namelist)


@mark.parametrize(("hours", "expected"), [(0.25, "00:15:00"), (120, "005_00:00:00")])
def test_MPAS_namelist_file__durations(config, cycle, expected, hours, logged):
    config["mpas"]["length"] = hours
    driverobj = MPAS(config=config, cycle=cycle)
    dst = driverobj.rundir / "namelist.atmosphere"
    assert not dst.is_file()
    path = Path(driverobj.namelist_file().ref)
    assert dst.is_file()
    assert logged(f"Wrote config to {path}")
    nml = f90nml.read(dst)
    assert isinstance(nml, f90nml.Namelist)
    assert nml["nhyd_model"]["config_run_duration"] == expected


def test_MPAS_namelist_file__fails_validation(driverobj, logged):
    driverobj._config["namelist"]["update_values"]["nhyd_model"]["foo"] = None
    path = Path(driverobj.namelist_file().ref)
    assert not path.exists()
    assert logged(f"Failed to validate {path}")
    assert logged("  None is not of type 'array', 'boolean', 'number', 'string'")


def test_MPAS_namelist_file__missing_base_file(driverobj, logged):
    base_file = str(Path(driverobj.config["rundir"], "missing.nml"))
    driverobj._config["namelist"]["base_file"] = base_file
    path = Path(driverobj.namelist_file().ref)
    assert not path.exists()
    assert logged("missing.nml: Not ready [external asset]")


def test_MPAS_output__filename_interval_none(driverobj, outpath):
    driverobj._config["streams"]["output"].update(
        {"filename_interval": "none", "filename_template": "$Y-$M-$D_$d_$h-$m-$s.nc"},
    )
    assert driverobj.output["paths"] == [outpath("2024-02-01_032_18-00-00.nc")]


def test_MPAS_output__filename_interval_output_interval_initial_only(driverobj, outpath):
    driverobj._config["streams"]["output"].update(
        {"filename_template": "$Y-$M-$D_$d_$h-$m-$s.nc", "output_interval": "initial_only"}
    )
    assert driverobj.output["paths"] == [outpath("2024-02-01_032_18-00-00.nc")]


@mark.parametrize("explicit", [True, False])
def test_MPAS_output__filename_interval_output_interval_none(driverobj, explicit):
    updates = {"output_interval": "none"}
    if explicit:
        updates["filename_interval"] = "output_interval"
    driverobj._config["streams"]["output"].update(updates)
    assert driverobj.output["paths"] == []


@mark.parametrize("explicit", [True, False])
def test_MPAS_output__filename_interval_output_interval_timestamp(driverobj, explicit, outpath):
    updates = {"filename_template": "$Y-$M-$D_$d_$h-$m-$s.nc", "output_interval": "01:00:00"}
    if explicit:
        updates["filename_interval"] = "output_interval"
    driverobj._config["streams"]["output"].update(updates)
    assert driverobj.output["paths"] == [
        outpath("2024-02-01_032_18-00-00.nc"),
        outpath("2024-02-01_032_19-00-00.nc"),
    ]


def test_MPAS_output__filename_interval_timestamp(driverobj, outpath):
    updates = {
        "filename_interval": "1_00:00:00",
        "filename_template": "$Y-$M-$D_$d_$h-$m-$s.nc",
        "output_interval": "06:00:00",
    }
    driverobj._config["streams"]["output"].update(updates)
    driverobj._config["length"] = 36
    assert driverobj.output["paths"] == [
        outpath("2024-02-01_032_18-00-00.nc"),
        outpath("2024-02-02_033_18-00-00.nc"),
    ]


def test_MPAS_output__filename_interval_timestamp_reference_time(driverobj, outpath):
    updates = {
        "filename_interval": "1_00:00:00",
        "filename_template": "$Y-$M-$D_$d_$h-$m-$s.nc",
        "output_interval": "06:00:00",
        "reference_time": "2024-02-01_00:00:00",
    }
    driverobj._config["streams"]["output"].update(updates)
    driverobj._config["length"] = 36
    assert driverobj.output["paths"] == [
        outpath("2024-02-01_032_00-00-00.nc"),
        outpath("2024-02-02_033_00-00-00.nc"),
    ]


def test_MPAS_output__non_output_stream(driverobj):
    driverobj._config["streams"]["output"].update({"type": "input"})
    assert driverobj.output["paths"] == []


@mark.parametrize("domain", ["global", "regional"])
def test_MPAS_provisioned_rundir(domain, driverobj, ready_task):
    driverobj._config["domain"] = domain
    with patch.multiple(
        driverobj,
        boundary_files=ready_task,
        files_copied=ready_task,
        files_hardlinked=ready_task,
        files_linked=ready_task,
        namelist_file=ready_task,
        runscript=ready_task,
        streams_file=ready_task,
    ):
        assert driverobj.provisioned_rundir().ready


def test_MPAS_streams_file(config, driverobj):
    streams_file(config, driverobj, "mpas")


@mark.parametrize(
    ("dtargs", "interval", "reference_time"),
    [
        ([(2024, 2, 1), (2024, 2, 2)], "1_00:00:00", "2024-02-01_00:00:00"),
        ([(2024, 2, 1, 18), (2024, 2, 2, 12), (2024, 2, 3, 6)], "18:00:00", None),
        ([(2024, 2, 1, 18), (2024, 2, 2, 18)], "1_00:00:00", None),
    ],
)
def test_MPAS__filename_interval_timestamps(driverobj, dtargs, interval, reference_time):
    driverobj._config["length"] = 36
    expected = [datetime(*args, tzinfo=timezone.utc) for args in dtargs]  # type: ignore[misc]
    assert (
        driverobj._filename_interval_timestamps(interval=interval, reference_time=reference_time)
        == expected
    )


def test_MPAS__initial_and_final_ts(driverobj):
    initial = driverobj._cycle.replace(tzinfo=timezone.utc)
    final = initial + timedelta(hours=1)
    assert driverobj._initial_and_final_ts == (initial, final)


@mark.parametrize(
    ("dtargs", "interval", "length"),
    [
        ([(2024, 2, 1, 18), (2024, 2, 2, 18), (2024, 2, 3, 18)], "1_00:00:00", 48),
        ([(2024, 2, 1, 18), (2024, 2, 2, 6)], "12:00:00", 18),
    ],
)
def test_MPAS__interval_timestamps(driverobj, dtargs, interval, length):
    driverobj._config["length"] = length
    expected = [datetime(*args, tzinfo=timezone.utc) for args in dtargs]  # type: ignore[misc]
    assert driverobj._interval_timestamps(interval=interval) == expected


def test_MPAS__output_path(driverobj):
    t = "out.$Y_$M_$D-$d-$h_$m_$s.nc"
    d = datetime(2025, 5, 7, 1, 2, 3, tzinfo=timezone.utc)
    expected = driverobj.rundir / "out.2025_05_07-127-01_02_03.nc"
    assert driverobj._output_path(template=t, dtobj=d) == expected


def test_MPAS__streams_fn(driverobj):
    assert driverobj._streams_fn == "streams.atmosphere"
