"""
MPASInit driver tests.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import f90nml  # type: ignore[import-untyped]
from pytest import fixture, mark

from uwtools.drivers.mpas_init import MPASInit
from uwtools.tests.drivers.test_mpas import streams_file
from uwtools.tests.support import fixture_path

# Fixtures


@fixture
def config(tmp_path):
    return {
        "mpas_init": {
            "boundary_conditions": {
                "interval_hours": 1,
                "length": 1,
                "offset": 0,
                "path": str(tmp_path / "input_path"),
            },
            "execution": {
                "batchargs": {
                    "walltime": "01:30:00",
                },
                "executable": "mpas_init",
            },
            "files_to_link": {
                "CAM_ABS_DATA.DBL": "src/MPAS-Model/CAM_ABS_DATA.DBL",
                "CAM_AEROPT_DATA.DBL": "src/MPAS-Model/CAM_AEROPT_DATA.DBL",
                "GENPARM.TBL": "src/MPAS-Model/GENPARM.TBL",
                "LANDUSE.TBL": "src/MPAS-Model/LANDUSE.TBL",
                "OZONE_DAT.TBL": "src/MPAS-Model/OZONE_DAT.TBL",
                "OZONE_LAT.TBL": "src/MPAS-Model/OZONE_LAT.TBL",
                "OZONE_PLEV.TBL": "src/MPAS-Model/OZONE_PLEV.TBL",
                "RRTMG_LW_DATA": "src/MPAS-Model/RRTMG_LW_DATA",
                "RRTMG_LW_DATA.DBL": "src/MPAS-Model/RRTMG_LW_DATA.DBL",
                "RRTMG_SW_DATA": "src/MPAS-Model/RRTMG_SW_DATA",
                "RRTMG_SW_DATA.DBL": "src/MPAS-Model/RRTMG_SW_DATA.DBL",
                "SOILPARM.TBL": "src/MPAS-Model/SOILPARM.TBL",
                "VEGPARM.TBL": "src/MPAS-Model/VEGPARM.TBL",
            },
            "namelist": {
                "base_file": str(fixture_path("simple.nml")),
                "update_values": {
                    "nhyd_model": {"config_start_time": "12", "config_stop_time": "12"},
                },
            },
            "rundir": str(tmp_path),
            "streams": {
                "input": {
                    "filename_template": "conus.static.nc",
                    "input_interval": "initial_only",
                    "mutable": False,
                    "type": "input",
                },
                "output": {
                    "filename_template": "conus.init.nc",
                    "files": ["stream_list.atmosphere.output"],
                    "mutable": False,
                    "output_interval": "initial_only",
                    "streams": ["stream1", "stream2"],
                    "type": "output",
                    "var_arrays": ["va1", "va2"],
                    "var_structs": ["vs1", "vs2"],
                    "vars": ["v1", "v2"],
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
    return MPASInit(config=config, cycle=cycle, batch=True)


@fixture
def outpath(driverobj):
    return lambda fn: driverobj.rundir / fn


# Tests


def test_MPASInit_boundary_files(cycle, driverobj):
    ns = (0, 1)
    links = [
        driverobj.rundir / f"FILE:{(cycle + timedelta(hours=n)).strftime('%Y-%m-%d_%H')}"
        for n in ns
    ]
    assert not any(link.is_file() for link in links)
    input_path = Path(driverobj.config["boundary_conditions"]["path"])
    input_path.mkdir()
    for n in ns:
        (input_path / f"FILE:{(cycle + timedelta(hours=n)).strftime('%Y-%m-%d_%H')}").touch()
    driverobj.boundary_files()
    assert all(link.is_symlink() for link in links)


def test_MPASInit_driver_name(driverobj):
    assert driverobj.driver_name() == MPASInit.driver_name() == "mpas_init"


@mark.parametrize(
    ("key", "task", "test"),
    [("files_to_copy", "files_copied", "is_file"), ("files_to_link", "files_linked", "is_symlink")],
)
def test_MPASInit_files_copied_and_files_linked(config, cycle, key, task, test, tmp_path):
    atm, sfc = "gfs.t%sz.atmanl.nc", "gfs.t%sz.sfcanl.nc"
    atm_cfg_dst, sfc_cfg_dst = [x % "{{ cycle.strftime('%H') }}" for x in [atm, sfc]]
    atm_cfg_src, sfc_cfg_src = [str(tmp_path / (x + ".in")) for x in [atm_cfg_dst, sfc_cfg_dst]]
    config["mpas_init"].update({key: {atm_cfg_dst: atm_cfg_src, sfc_cfg_dst: sfc_cfg_src}})
    driverobj = MPASInit(config=config, cycle=cycle, batch=True)
    atm_dst, sfc_dst = [tmp_path / (x % cycle.strftime("%H")) for x in [atm, sfc]]
    assert not any(dst.is_file() for dst in [atm_dst, sfc_dst])
    atm_src, sfc_src = [Path(str(x) + ".in") for x in [atm_dst, sfc_dst]]
    for src in (atm_src, sfc_src):
        src.touch()
    getattr(driverobj, task)()
    assert all(getattr(dst, test)() for dst in [atm_dst, sfc_dst])


def test_MPASInit_namelist_file(driverobj, logged):
    dst = driverobj.rundir / "namelist.init_atmosphere"
    assert not dst.is_file()
    path = Path(driverobj.namelist_file().ref)
    assert dst.is_file()
    assert logged(f"Wrote config to {path}")
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_MPASInit_namelist_file__contents(cycle, driverobj):
    dst = driverobj.rundir / "namelist.init_atmosphere"
    assert not dst.is_file()
    driverobj.namelist_file()
    assert dst.is_file()
    nml = f90nml.read(dst)
    stop_time = cycle + timedelta(hours=1)
    f = "%Y-%m-%d_%H:00:00"
    assert nml["nhyd_model"]["config_start_time"] == cycle.strftime(f)
    assert nml["nhyd_model"]["config_stop_time"] == stop_time.strftime(f)


def test_MPASInit_namelist_file__fails_validation(driverobj, logged):
    driverobj._config["namelist"]["update_values"]["nhyd_model"]["foo"] = None
    path = Path(driverobj.namelist_file().ref)
    assert not path.exists()
    assert logged(f"Failed to validate {path}")
    assert logged("  None is not of type 'array', 'boolean', 'number', 'string'")


def test_MPASInit_namelist_file__missing_base_file(driverobj, logged):
    base_file = str(Path(driverobj.config["rundir"], "missing.nml"))
    driverobj._config["namelist"]["base_file"] = base_file
    path = Path(driverobj.namelist_file().ref)
    assert not path.exists()
    assert logged("Not ready [external asset]")


def test_MPASInit_output__filename_interval_none(driverobj, outpath):
    driverobj._config["streams"]["output"].update(
        {"filename_interval": "none", "filename_template": "$Y-$M-$D_$d_$h-$m-$s.nc"},
    )
    assert driverobj.output["paths"] == [outpath("2024-02-01_032_18-00-00.nc")]


def test_MPASInit_output__filename_interval_output_interval_initial_only(driverobj, outpath):
    driverobj._config["streams"]["output"].update(
        {"filename_template": "$Y-$M-$D_$d_$h-$m-$s.nc", "output_interval": "initial_only"}
    )
    assert driverobj.output["paths"] == [outpath("2024-02-01_032_18-00-00.nc")]


@mark.parametrize("explicit", [True, False])
def test_MPASInit_output__filename_interval_output_interval_none(driverobj, explicit):
    updates = {"output_interval": "none"}
    if explicit:
        updates["filename_interval"] = "output_interval"
    driverobj._config["streams"]["output"].update(updates)
    assert driverobj.output["paths"] == []


@mark.parametrize("explicit", [True, False])
def test_MPASInit_output__filename_interval_output_interval_timestamp(driverobj, explicit, outpath):
    updates = {"filename_template": "$Y-$M-$D_$d_$h-$m-$s.nc", "output_interval": "01:00:00"}
    if explicit:
        updates["filename_interval"] = "output_interval"
    driverobj._config["streams"]["output"].update(updates)
    assert driverobj.output["paths"] == [
        outpath("2024-02-01_032_18-00-00.nc"),
        outpath("2024-02-01_032_19-00-00.nc"),
    ]


def test_MPASInit_output__filename_interval_timestamp(driverobj, outpath):
    updates = {
        "filename_interval": "1_00:00:00",
        "filename_template": "$Y-$M-$D_$d_$h-$m-$s.nc",
        "output_interval": "06:00:00",
    }
    driverobj._config["streams"]["output"].update(updates)
    driverobj._config["boundary_conditions"].update({"interval_hours": 6, "length": 36})
    assert driverobj.output["paths"] == [
        outpath("2024-02-01_032_18-00-00.nc"),
        outpath("2024-02-02_033_18-00-00.nc"),
    ]


def test_MPASInit_output__filename_interval_timestamp_reference_time(driverobj, outpath):
    updates = {
        "filename_interval": "1_00:00:00",
        "filename_template": "$Y-$M-$D_$d_$h-$m-$s.nc",
        "output_interval": "06:00:00",
        "reference_time": "2024-02-01_00:00:00",
    }
    driverobj._config["streams"]["output"].update(updates)
    driverobj._config["boundary_conditions"].update({"interval_hours": 6, "length": 36})
    assert driverobj.output["paths"] == [
        outpath("2024-02-01_032_00-00-00.nc"),
        outpath("2024-02-02_033_00-00-00.nc"),
    ]


def test_MPASInit_output__non_output_stream(driverobj):
    driverobj._config["streams"]["output"].update({"type": "input"})
    assert driverobj.output["paths"] == []


def test_MPASInit_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        boundary_files=ready_task,
        files_copied=ready_task,
        files_hardlinked=ready_task,
        files_linked=ready_task,
        namelist_file=ready_task,
        runscript=ready_task,
        streams_file=ready_task,
    ) as mocks:
        driverobj.provisioned_rundir()
    for m in mocks:
        mocks[m].assert_called_once_with()


def test_MPASInit_streams_file(config, driverobj):
    streams_file(config, driverobj, "mpas_init")


@mark.parametrize(
    ("dtargs", "interval", "reference_time"),
    [
        ([(2024, 2, 1), (2024, 2, 2)], "1_00:00:00", "2024-02-01_00:00:00"),
        ([(2024, 2, 1, 18), (2024, 2, 2, 12), (2024, 2, 3, 6)], "18:00:00", None),
        ([(2024, 2, 1, 18), (2024, 2, 2, 18)], "1_00:00:00", None),
    ],
)
def test_MPASInit__filename_interval_timestamps(driverobj, dtargs, interval, reference_time):
    driverobj._config["boundary_conditions"]["length"] = 36
    expected = [datetime(*args, tzinfo=timezone.utc) for args in dtargs]  # type: ignore[misc]
    assert (
        driverobj._filename_interval_timestamps(interval=interval, reference_time=reference_time)
        == expected
    )


def test_MPASInit__initial_and_final_ts(driverobj):
    initial = datetime(2024, 2, 1, 18, tzinfo=timezone.utc)
    final = initial + timedelta(hours=1)
    assert driverobj._initial_and_final_ts == (initial, final)


@mark.parametrize(
    ("dtargs", "interval", "length"),
    [
        ([(2024, 2, 1, 18), (2024, 2, 2, 18), (2024, 2, 3, 18)], "1_00:00:00", 48),
        ([(2024, 2, 1, 18), (2024, 2, 2, 6)], "12:00:00", 18),
    ],
)
def test_MPASInit__interval_timestamps(driverobj, dtargs, interval, length):
    driverobj._config["boundary_conditions"]["length"] = length
    expected = [datetime(*args, tzinfo=timezone.utc) for args in dtargs]  # type: ignore[misc]
    assert driverobj._interval_timestamps(interval=interval) == expected


def test_MPASInit__output_path(driverobj):
    t = "out.$Y_$M_$D-$d-$h_$m_$s.nc"
    d = datetime(2025, 5, 7, 1, 2, 3, tzinfo=timezone.utc)
    expected = driverobj.rundir / "out.2025_05_07-127-01_02_03.nc"
    assert driverobj._output_path(template=t, dtobj=d) == expected


def test_MPASInit__streams_fn(driverobj):
    assert driverobj._streams_fn == "streams.init_atmosphere"
