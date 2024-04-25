# pylint: disable=missing-function-docstring

from uwtools.api import jedi


def test_api_jedi_module_content():
    assert callable(jedi.execute)
    assert callable(jedi.graph)
    assert callable(jedi.tasks)
