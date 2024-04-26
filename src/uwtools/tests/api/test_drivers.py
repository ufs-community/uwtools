# pylint: disable=missing-function-docstring,protected-access

from datetime import datetime as dt
from unittest.mock import patch

import iotaa
import pytest

from uwtools.api import chgres_cube, fv3, jedi, mpas, mpas_init, sfc_climo_gen, ungrib
from uwtools.drivers import support
from uwtools.utils import api

modules = [chgres_cube, fv3, jedi, mpas_init, mpas, sfc_climo_gen, ungrib]
nocycle = [sfc_climo_gen]


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
