# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for the uwtools.config.base module.
"""

import logging
import os
from unittest.mock import patch

import pytest
import yaml
from pytest import fixture

from uwtools.config import tools
from uwtools.config.formats.base import Config
from uwtools.logging import log
from uwtools.tests.support import fixture_path, logged, regex_logged
from uwtools.utils.file import FORMAT, readable

# Fixtures


@fixture
def config(tmp_path):
    path = tmp_path / "config.yaml"
    data = {"foo": 88}
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)
    return ConcreteConfig(config_file=path)


# Helpers


class ConcreteConfig(Config):
    """
    Config subclass for testing purposes.
    """

    def _load(self, config_file):
        with readable(config_file) as f:
            return yaml.safe_load(f.read())

    def dump(self, path):
        pass

    @staticmethod
    def dump_dict(path, cfg, opts=None):
        pass


# Tests


def test___repr__(capsys, config):
    print(config)
    assert yaml.safe_load(capsys.readouterr().out)["foo"] == 88


def test__load_paths(config, tmp_path):
    paths = (tmp_path / fn for fn in ("f1", "f2"))
    for path in paths:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump({path.name: "defined"}, f)
    cfg = config._load_paths(config_files=paths)
    for path in paths:
        assert cfg[path.name] == "present"


def test_characterize_values(config):
    values = {1: "", 2: None, 3: "{{ n }}", 4: {"a": 88}, 5: [{"b": 99}], 6: "string"}
    complete, empty, template = config.characterize_values(values=values, parent="p")
    assert complete == ["    p4", "    p4.a", "    pb", "    p5", "    p6"]
    assert empty == ["    p1", "    p2"]
    assert template == ["    p3: {{ n }}"]


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
    assert not cfgobj.compare_config(cfgobj, salad_base)
    assert not cfgobj.compare_config(salad_base)
    # Expect to see the following differences logged:
    for msg in [
        "salad:        how_many:  - 12 + None",
        "salad:        dressing:  - balsamic + italian",
        "salad:            size:  - None + large",
    ]:
        assert logged(caplog, msg)


def test_depth(config):
    assert config.depth == 1


def test_dereference(caplog, config):
    # Test demonstrates that:
    #   - Config dereferencing uses environment variables.
    #   - Initially-unrenderable values do not cause errors.
    #   - Initially-unrenderable values may be rendered via iteration.
    #   - Finally-unrenderable values do not cause errors and are returned unmodified.
    log.setLevel(logging.DEBUG)
    config.data.update({"a": "{{ b.c + 11 }}", "b": {"c": "{{ N | int + 11 }}"}, "d": "{{ X }}"})
    with patch.dict(os.environ, {"N": "55"}, clear=True):
        config.dereference()
    for excerpt in [
        "'a': '{{ b.c + 11 }}', 'b': {'c': '{{ N | int + 11 }}'}, 'd': '{{ X }}'",
        "'a': '{{ b.c + 11 }}', 'b': {'c': 66}, 'd': '{{ X }}'",
        "'a': 77, 'b': {'c': 66}, 'd': '{{ X }}'",
    ]:
        assert regex_logged(caplog, excerpt)
    assert config == {"foo": 88, "a": 77, "b": {"c": 66}, "d": "{{ X }}"}


# NB: Need direct test for parse_include().

# NB: Need direct test for update_values().


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
