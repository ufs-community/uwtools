from pathlib import Path

import f90nml  # type: ignore[import-untyped]
from pytest import raises

from uwtools.drivers import upp_common
from uwtools.drivers.upp_common import NFIELDS, NPARAMS
from uwtools.exceptions import UWConfigError

# Tests:


def test_upp_common_control_file(upp_driverobj):
    control_file(upp_driverobj)


def test_upp_common_files_copied(upp_driverobj):
    files_copied(upp_driverobj)


def test_upp_files_linked(upp_driverobj):
    files_linked(upp_driverobj)


def test_upp_common_namelist_file(upp_driverobj, logged):
    namelist_file(upp_driverobj, logged)


def test_upp_common_namelist_file__fails_validation(upp_driverobj, logged):
    namelist_file__fails_validation(upp_driverobj, logged)


def test_upp_common_namelist_file__missing_base_file(upp_driverobj, logged):
    namelist_file__missing_base_file(upp_driverobj, logged)


def test_upp_common_output(upp_driverobj, tmp_path):
    output(upp_driverobj, tmp_path)


def test_upp_common_output__fail(upp_driverobj):
    output__fail(upp_driverobj)


def test_upp_common_namelist_path(upp_driverobj):
    assert upp_common.namelist_path(upp_driverobj) == upp_driverobj.rundir / "itag"


# Helpers:


def control_file(upp_driverobj):
    cfg = upp_driverobj._config
    rundir = Path(cfg["rundir"])
    path = rundir.parent / "src"
    contents = "control file contents"
    path.write_text(contents)
    cfg["control_file"] = str(path)
    task = upp_driverobj.control_file()
    assert task.ready
    assert task.ref[0].read_text() == contents


def files_copied(upp_driverobj):
    for src in upp_driverobj.config["files_to_copy"].values():
        Path(src).touch()
    for dst in upp_driverobj.config["files_to_copy"]:
        assert not (upp_driverobj.rundir / dst).is_file()
    upp_driverobj.files_copied()
    for dst in upp_driverobj.config["files_to_copy"]:
        assert (upp_driverobj.rundir / dst).is_file()


def files_linked(upp_driverobj):
    for src in upp_driverobj.config["files_to_link"].values():
        Path(src).touch()
    for dst in upp_driverobj.config["files_to_link"]:
        assert not (upp_driverobj.rundir / dst).is_file()
    upp_driverobj.files_linked()
    for dst in upp_driverobj.config["files_to_link"]:
        assert (upp_driverobj.rundir / dst).is_symlink()


def namelist_file(upp_driverobj, logged):
    datestr = "2024-05-05_12:00:00"
    base_file = Path(upp_driverobj.config["namelist"]["base_file"])
    base_file.write_text("&model_inputs datestr='%s' / &nampgb kpv=42 /" % datestr)
    dst = upp_driverobj.rundir / "itag"
    assert not dst.is_file()
    path = Path(upp_driverobj.namelist_file().ref)
    assert dst.is_file()
    assert logged(f"Wrote config to {path}")
    nml = f90nml.read(dst)
    assert isinstance(nml, f90nml.Namelist)
    assert nml["model_inputs"]["datestr"] == datestr
    assert nml["model_inputs"]["grib"] == "grib2"
    assert nml["nampgb"]["kpo"] == 3
    assert nml["nampgb"]["kpv"] == 42


def namelist_file__fails_validation(upp_driverobj, logged):
    upp_driverobj._config["namelist"]["update_values"]["nampgb"]["kpo"] = "string"
    del upp_driverobj._config["namelist"]["base_file"]
    path = Path(upp_driverobj.namelist_file().ref)
    assert not path.exists()
    assert logged(f"Failed to validate {path}")
    assert logged("  'string' is not of type 'integer'")


def namelist_file__missing_base_file(upp_driverobj, logged):
    base_file = str(Path(upp_driverobj.config["rundir"], "missing.nml"))
    upp_driverobj._config["namelist"]["base_file"] = base_file
    path = Path(upp_driverobj.namelist_file().ref)
    assert not path.exists()
    assert logged("missing.nml: Not ready [external asset]")


def output(upp_driverobj, tmp_path):
    fields = ["?"] * (NFIELDS - 1)
    parameters = ["?"] * NPARAMS
    # fmt: off
    control_data = [
        "2",                # number of blocks
        "1",                # number variables in 2nd block
        "2",                # number variables in 1st block
        "FOO",              # 1st block identifier
        *fields,            # 1st block fields
        *(parameters * 2) , # 1st block variable parameters
        "BAR",              # 2nd block identifier
        *fields,            # 2nd block fields
        *parameters,        # 2nd block variable parameters
    ]
    # fmt: on
    control_file = tmp_path / "postxconfig-NT.txt"
    control_file.write_text("\n".join(control_data))
    upp_driverobj._config["control_file"] = str(control_file)
    expected = {"paths": [upp_driverobj.rundir / ("%s.GrbF24" % x) for x in ("FOO", "BAR")]}
    assert upp_driverobj.output == expected


def output__fail(upp_driverobj):
    with raises(UWConfigError) as e:
        assert upp_driverobj.output
    assert (
        str(e.value) == "Could not open UPP control file %s" % upp_driverobj.config["control_file"]
    )
