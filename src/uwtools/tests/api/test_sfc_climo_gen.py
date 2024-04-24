# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

from uwtools.api import sfc_climo_gen


def test_api_sfc_climo_gen_module_content():
    assert callable(sfc_climo_gen.execute)
    assert callable(sfc_climo_gen.graph)
    assert callable(sfc_climo_gen.tasks)
