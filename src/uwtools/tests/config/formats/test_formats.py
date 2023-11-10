"""
Tests for the uwtools.config.formats package.
"""

import logging

import pytest
import yaml
from pytest import fixture

from uwtools.config import tools
from uwtools.logging import log
from uwtools.tests.config.formats.support import salad_base
from uwtools.tests.support import fixture_path, logged
from uwtools.utils.file import FORMAT

# Fixtures


@fixture
def nml_cfgobj(tmp_path):
    # Use NMLConfig to exercise methods in Config abstract base class.
    path = tmp_path / "cfg.nml"
    with open(path, "w", encoding="utf-8") as f:
        f.write("&nl n = 88 /")
    return tools.format_to_config(FORMAT.nml)(config_file=path)


# Tests


def test_Config___repr__(capsys, nml_cfgobj):
    print(nml_cfgobj)
    assert yaml.safe_load(capsys.readouterr().out)["nl"]["n"] == 88


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


@pytest.mark.parametrize("fmt1", [FORMAT.ini, FORMAT.nml, FORMAT.yaml])
@pytest.mark.parametrize("fmt2", [FORMAT.ini, FORMAT.nml, FORMAT.yaml])
def test_transform_config(fmt1, fmt2, tmp_path):
    """
    Test that transforms config objects to objects of other config subclasses.
    """
    outfile = tmp_path / f"test_{fmt1.lower()}to{fmt2.lower()}_dump.{fmt2}"
    reference = fixture_path(f"simple.{fmt2}")
    cfgin = tools.format_to_config(fmt1)(fixture_path(f"simple.{fmt1}"))
    tools.format_to_config(fmt2).dump_dict(path=outfile, cfg=cfgin.data)
    with open(reference, "r", encoding="utf-8") as f1:
        reflines = [line.strip().replace("'", "") for line in f1]
    with open(outfile, "r", encoding="utf-8") as f2:
        outlines = [line.strip().replace("'", "") for line in f2]
    for line1, line2 in zip(reflines, outlines):
        assert line1 == line2
