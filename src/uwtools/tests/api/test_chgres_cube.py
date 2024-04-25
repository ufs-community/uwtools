# pylint: disable=missing-function-docstring

from uwtools.api import chgres_cube


def test_api_chgres_cube_module_content():
    assert callable(chgres_cube.execute)
    assert callable(chgres_cube.graph)
    assert callable(chgres_cube.tasks)
