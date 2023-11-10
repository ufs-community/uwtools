# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.config.tools module.
"""

import logging

import yaml
from pytest import fixture, raises

from uwtools.config import tools
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.tests.support import logged
from uwtools.utils.file import FORMAT, writable

# Fixtures


@fixture
def compare_configs_assets(tmp_path):
    d = {"foo": {"bar": 88}, "baz": {"qux": 99}}
    a = tmp_path / "a"
    b = tmp_path / "b"
    with writable(a) as f:
        yaml.dump(d, f)
    with writable(b) as f:
        yaml.dump(d, f)
    return d, a, b


# Tests


def test_compare_configs_good(compare_configs_assets, caplog):
    log.setLevel(logging.INFO)
    _, a, b = compare_configs_assets
    assert tools.compare_configs(
        config_a_path=a, config_a_format=FORMAT.yaml, config_b_path=b, config_b_format=FORMAT.yaml
    )
    assert caplog.records


def test_compare_configs_changed_value(compare_configs_assets, caplog):
    log.setLevel(logging.INFO)
    d, a, b = compare_configs_assets
    d["baz"]["qux"] = 11
    with writable(b) as f:
        yaml.dump(d, f)
    assert not tools.compare_configs(
        config_a_path=a, config_a_format=FORMAT.yaml, config_b_path=b, config_b_format=FORMAT.yaml
    )
    assert logged(caplog, "baz:             qux:  - 99 + 11")


def test_compare_configs_missing_key(compare_configs_assets, caplog):
    log.setLevel(logging.INFO)
    d, a, b = compare_configs_assets
    del d["baz"]
    with writable(b) as f:
        yaml.dump(d, f)
    # Note that a and b are swapped:
    assert not tools.compare_configs(
        config_a_path=b, config_a_format=FORMAT.yaml, config_b_path=a, config_b_format=FORMAT.yaml
    )
    assert logged(caplog, "baz:             qux:  - None + 99")


def test_compare_configs_bad_format(caplog):
    log.setLevel(logging.INFO)
    with raises(UWConfigError) as e:
        tools.compare_configs(
            config_a_path="/not/used",
            config_a_format="jpg",
            config_b_path="/not/used",
            config_b_format=FORMAT.yaml,
        )
    msg = "Format 'jpg' should be one of: fieldtable, ini, nml, yaml"
    assert logged(caplog, msg)
    assert msg in str(e.value)
