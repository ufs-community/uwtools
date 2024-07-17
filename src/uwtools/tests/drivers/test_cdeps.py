# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
CDEPS driver tests.
"""

import datetime as dt
import logging
from copy import deepcopy
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import f90nml  # type: ignore
from iotaa import refs
from pytest import fixture, mark

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers import cdeps
from uwtools.drivers.cdeps import CDEPS
from uwtools.logging import log
from uwtools.tests.support import logged
from uwtools.tests.test_schemas import CDEPS_CONFIG

# Fixtures


@fixture
def driverobj(tmp_path):
    return CDEPS(
        config={"cdeps": {**deepcopy(CDEPS_CONFIG), "rundir": str(tmp_path)}},
        cycle=dt.datetime.now(),
    )


# Tests


def test_CDEPS_atm(driverobj):
    with patch.object(CDEPS, "atm_nml") as atm_nml:
        with patch.object(CDEPS, "atm_stream") as atm_stream:
            driverobj.atm()
        atm_stream.assert_called_once_with()
    atm_nml.assert_called_once_with()


@mark.parametrize("group", ["atm", "ocn"])
def test_CDEPS_nml(caplog, driverobj, group):
    log.setLevel(logging.DEBUG)
    dst = driverobj._rundir / f"d{group}_in"
    assert not dst.is_file()
    del driverobj._driver_config[f"{group}_in"]["base_file"]
    task = getattr(driverobj, f"{group}_nml")
    path = Path(refs(task()))
    assert dst.is_file()
    assert logged(caplog, f"Wrote config to {path}")
    assert isinstance(f90nml.read(dst), f90nml.Namelist)


def test_CDEPS_ocn(driverobj):
    with patch.object(CDEPS, "ocn_nml") as ocn_nml:
        with patch.object(CDEPS, "ocn_stream") as ocn_stream:
            driverobj.ocn()
        ocn_stream.assert_called_once_with()
    ocn_nml.assert_called_once_with()


def test_CDEPS_provisioned_rundir(driverobj):
    with patch.object(CDEPS, "atm") as atm:
        with patch.object(CDEPS, "ocn") as ocn:
            driverobj.provisioned_rundir()
        ocn.assert_called_once_with()
    atm.assert_called_once_with()


@mark.parametrize("group", ["atm", "ocn"])
def test_CDEP_streams(driverobj, group):
    dst = driverobj._rundir / f"d{group}.streams"
    assert not dst.is_file()
    template = """
    {{ stream01.dtlimit }}
    {{ stream01.mapalgo }}
    {{ stream01.readmode }}
    {{ " ".join(stream01.stream_data_files) }}
    {{ " ".join(stream01.stream_data_variables) }}
    {{ stream01.stream_lev_dimname }}
    {{ stream01.stream_mesh_file }}
    {{ stream01.stream_offset }}
    {{ " ".join(stream01.stream_vectors) }}
    {{ stream01.taxmode }}
    {{ stream01.tinterpalgo }}
    {{ stream01.yearAlign }}
    {{ stream01.yearFirst }}
    {{ stream01.yearLast }}
    """
    template_file = driverobj._rundir / "template.jinja2"
    with open(template_file, "w", encoding="utf-8") as f:
        print(dedent(template).strip(), file=f)
    driverobj._driver_config[f"{group}_streams"]["template_file"] = template_file
    task = getattr(driverobj, f"{group}_stream")
    path = Path(refs(task()))
    assert dst.is_file()
    expected = """
    1.5
    string
    single
    string string
    string string
    string
    string
    1
    u v
    string
    string
    1
    1
    1
    """
    with open(path, "r", encoding="utf-8") as f:
        assert f.read().strip() == dedent(expected).strip()


def test_CDEPS__driver_name(driverobj):
    assert driverobj._driver_name == "cdeps"


def test_CDEPS__model_namelist_file(driverobj):
    group = "atm_in"
    path = Path("/path/to/some.nml")
    with patch.object(driverobj, "_create_user_updated_config") as cuuc:
        driverobj._model_namelist_file(group=group, path=path)
        cuuc.assert_called_once_with(
            config_class=NMLConfig, config_values=driverobj._driver_config[group], path=path
        )


def test_CDEPS__model_stream_file(driverobj):
    group = "atm_streams"
    path = Path("/path/to/some.streams")
    template_file = Path("/path/to/some.jinja2")
    with patch.object(cdeps, "_render") as render:
        driverobj._model_stream_file(group=group, path=path, template_file=template_file)
        render.assert_called_once_with(
            input_file=template_file,
            output_file=path,
            values_src=driverobj._driver_config[group]["streams"],
        )
