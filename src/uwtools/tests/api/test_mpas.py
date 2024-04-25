# pylint: disable=missing-function-docstring

from uwtools.api import mpas


def test_api_mpas_module_content():
    assert callable(mpas.execute)
    assert callable(mpas.graph)
    assert callable(mpas.tasks)
