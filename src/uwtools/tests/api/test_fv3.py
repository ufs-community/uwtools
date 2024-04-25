# pylint: disable=missing-function-docstring

from uwtools.api import fv3


def test_api_fv3_module_content():
    assert callable(fv3.execute)
    assert callable(fv3.graph)
    assert callable(fv3.tasks)
