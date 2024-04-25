# pylint: disable=missing-function-docstring

from uwtools.api import ungrib


def test_api_ungrib_module_content():
    assert callable(ungrib.execute)
    assert callable(ungrib.graph)
    assert callable(ungrib.tasks)
