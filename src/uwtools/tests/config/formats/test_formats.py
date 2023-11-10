"""
Tests for the uwtools.config.formats package.
"""

import logging

import pytest

from uwtools.config import tools
from uwtools.logging import log
from uwtools.tests.config.formats.support import salad_base
from uwtools.tests.support import fixture_path, logged
from uwtools.utils.file import FORMAT

# Tests


@pytest.mark.parametrize("fmt", [FORMAT.ini, FORMAT.nml, FORMAT.yaml])
def test_compare_config(caplog, fmt, salad_base):
    """
    Compare two config objects.
    """
    log.setLevel(logging.INFO)
    cfgobj = tools.format_to_config(fmt)(fixture_path(f"simple.{fmt}"))
    if fmt == FORMAT.ini:
        salad_base["salad"]["how_many"] = "12"  # str "12" (not int 12) for ini
    assert cfgobj.compare_config(salad_base) is True
    # Expect no differences:
    assert not caplog.records
    caplog.clear()
    # Create differences in base dict:
    salad_base["salad"]["dressing"] = "italian"
    salad_base["salad"]["size"] = "large"
    del salad_base["salad"]["how_many"]
    # assert not cfgobj.compare_config(cfgobj, salad_base)
    assert not cfgobj.compare_config(salad_base)
    # Expect to see the following differences logged:
    for msg in [
        "salad:        how_many:  - 12 + None",
        "salad:        dressing:  - balsamic + italian",
        "salad:            size:  - None + large",
    ]:
        assert logged(caplog, msg)
