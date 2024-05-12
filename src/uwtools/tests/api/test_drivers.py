# pylint: disable=missing-function-docstring,protected-access

import datetime as dt
from unittest.mock import patch

import iotaa
import pytest

from uwtools.api import (
    chgres_cube,
    esg_grid,
    fv3,
    global_equiv_resol,
    jedi,
    make_hgrid,
    make_solo_mosaic,
    mpas,
    mpas_init,
    sfc_climo_gen,
    shave,
    ungrib,
    upp,
)
from uwtools.drivers import support
from uwtools.utils import api

modules = [
    chgres_cube,
    esg_grid,
    fv3,
    global_equiv_resol,
    jedi,
    make_hgrid,
    mpas,
    mpas_init,
    sfc_climo_gen,
    shave,
    ungrib,
    upp,
]
with_cycle = [chgres_cube, fv3, jedi, mpas, mpas_init, ungrib, upp]
with_leadtime = [upp]


@pytest.mark.parametrize("module", modules)
def test_api_execute(module):
    kwbase = {
        "batch": True,
        "config": "/some/config",
        "dry_run": True,
        "graph_file": "/some/g.dot",
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
            driver_class=module._Driver,
            cycle=kwargs["cycle"] if module in with_cycle else None,
            leadtime=kwargs["leadtime"] if module in with_leadtime else None,
            **kwbase
        )


@pytest.mark.parametrize("module", modules)
def test_api_graph(module):
    assert module.graph is support.graph


@pytest.mark.parametrize("module", modules)
def test_api_tasks(module):
    with patch.object(iotaa, "tasknames") as tasknames:
        module.tasks()
        tasknames.assert_called_once_with(module._Driver)
