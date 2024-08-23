# pylint: disable=missing-function-docstring,protected-access

import datetime as dt
from unittest.mock import patch

import iotaa
from pytest import mark

from uwtools.api import (
    cdeps,
    chgres_cube,
    esg_grid,
    filter_topo,
    fv3,
    global_equiv_resol,
    ioda,
    jedi,
    make_hgrid,
    make_solo_mosaic,
    mpas,
    mpas_init,
    orog,
    orog_gsl,
    schism,
    sfc_climo_gen,
    shave,
    ungrib,
    upp,
    ww3,
)
from uwtools.drivers import support
from uwtools.utils import api

modules = [
    cdeps,
    chgres_cube,
    esg_grid,
    filter_topo,
    fv3,
    global_equiv_resol,
    ioda,
    jedi,
    make_hgrid,
    make_solo_mosaic,
    mpas,
    mpas_init,
    orog,
    orog_gsl,
    schism,
    sfc_climo_gen,
    shave,
    ungrib,
    upp,
    ww3,
]
with_cycle = [cdeps, chgres_cube, fv3, ioda, jedi, mpas, mpas_init, schism, ungrib, upp, ww3]
with_leadtime = [upp]


@mark.parametrize("module", modules)
def test_api_execute(module):
    kwbase = {
        "batch": True,
        "config": "/some/config",
        "dry_run": False,
        "graph_file": "/some/g.dot",
        "key_path": None,
        "stdin_ok": True,
        "task": "foo",
    }
    kwargs = {
        **kwbase,
        **({"cycle": dt.datetime.now()} if module in with_cycle else {}),
        **({"leadtime": dt.timedelta(hours=24)} if module in with_leadtime else {}),
    }
    with patch.object(api, "_execute") as _execute:
        module.execute(**kwargs)
        _execute.assert_called_once_with(
            driver_class=module._driver,
            cycle=kwargs["cycle"] if module in with_cycle else None,
            leadtime=kwargs["leadtime"] if module in with_leadtime else None,
            **kwbase
        )


@mark.parametrize("module", modules)
def test_api_graph(module):
    assert module.graph is support.graph


@mark.parametrize("module", modules)
def test_api_schema(module):
    assert module.schema()


@mark.parametrize("module", modules)
def test_api_tasks(module):
    with patch.object(iotaa, "tasknames") as tasknames:
        module.tasks()
        tasknames.assert_called_once_with(module._driver)
