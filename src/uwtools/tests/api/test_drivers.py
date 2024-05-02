# pylint: disable=missing-function-docstring,protected-access

from datetime import datetime as dt
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
    ungrib,
)
from uwtools.drivers import support
from uwtools.utils import api

modules = [
    chgres_cube,
    esg_grid,
    fv3,
    jedi,
    make_hgrid,
    make_solo_mosaic,
    mpas,
    mpas_init,
    sfc_climo_gen,
    ungrib,
]
nocycle = [esg_grid, global_equiv_resol, make_hgrid, make_solo_mosaic, sfc_climo_gen]


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
    kwargs = kwbase if module in nocycle else {"cycle": dt.now(), **kwbase}
    with patch.object(api, "_execute") as _execute:
        module.execute(**kwargs)
        _execute.assert_called_once_with(
            driver_class=module._Driver,
            cycle=None if module in nocycle else kwargs["cycle"],
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
