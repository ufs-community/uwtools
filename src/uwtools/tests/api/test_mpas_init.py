# pylint: disable=missing-function-docstring

from uwtools.api import mpas_init


def test_api_mpas_init_module_content():
    assert callable(mpas_init.execute)
    assert callable(mpas_init.graph)
    assert callable(mpas_init.tasks)
