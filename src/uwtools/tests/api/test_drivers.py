import datetime as dt
from unittest.mock import patch

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
    mpassit,
    orog,
    orog_gsl,
    schism,
    sfc_climo_gen,
    shave,
    ungrib,
    upp,
    upp_assets,
    ww3,
)
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
    mpassit,
    orog,
    orog_gsl,
    schism,
    sfc_climo_gen,
    shave,
    ungrib,
    upp,
    upp_assets,
    ww3,
]
with_cycle = [
    cdeps,
    chgres_cube,
    fv3,
    ioda,
    jedi,
    mpas,
    mpas_init,
    mpassit,
    schism,
    ungrib,
    upp,
    upp_assets,
    ww3,
]
with_leadtime = [mpassit, upp, upp_assets]


@mark.parametrize("module", modules)
def test_api_execute(module, utc):
    kwbase = {
        "batch": True,
        "config": "/some/config",
        "dry_run": False,
        "graph_file": "/some/g.dot",
        "key_path": None,
        "schema_file": None,
        "stdin_ok": True,
        "task": "foo",
    }
    kwargs = {
        **kwbase,
        **({"cycle": utc()} if module in with_cycle else {}),
        **({"leadtime": dt.timedelta(hours=24)} if module in with_leadtime else {}),
    }
    with patch.object(api, "_execute") as _execute:
        module.execute(**kwargs)
        _execute.assert_called_once_with(
            driver_class=module._driver,
            cycle=kwargs["cycle"] if module in with_cycle else None,
            leadtime=kwargs["leadtime"] if module in with_leadtime else None,
            **kwbase,
        )


@mark.parametrize("module", modules)
def test_api_schema(module):
    assert module.schema()


@mark.parametrize("module", modules)
def test_api_tasks(module):
    with patch.object(module, "_tasks") as _tasks:
        module.tasks()
        _tasks.assert_called_once_with(module._driver)
