# pylint: disable=missing-function-docstring
"""
Tests for uwtools.config.jinja2 module.
"""

import logging
from collections import OrderedDict
from datetime import datetime

import yaml
from pytest import fixture, mark, raises

from uwtools.config import support
from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.config.formats.ini import INIConfig
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.sh import SHConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError, UWError
from uwtools.logging import log
from uwtools.tests.support import logged
from uwtools.utils.file import FORMAT


@mark.parametrize("d,n", [({1: 42}, 1), ({1: {2: 42}}, 2), ({1: {2: {3: 42}}}, 3), ({1: {}}, 2)])
def test_depth(d, n):
    assert support.depth(d) == n


@mark.parametrize(
    "cfgtype,fmt",
    [
        (FieldTableConfig, FORMAT.fieldtable),
        (INIConfig, FORMAT.ini),
        (NMLConfig, FORMAT.nml),
        (SHConfig, FORMAT.sh),
        (YAMLConfig, FORMAT.yaml),
    ],
)
def test_format_to_config(cfgtype, fmt):
    assert support.format_to_config(fmt) is cfgtype


def test_format_to_config_fail():
    with raises(UWConfigError):
        support.format_to_config("no-such-config-type")


def test_from_od():
    assert support.from_od(d=OrderedDict([("example", OrderedDict([("key", "value")]))])) == {
        "example": {"key": "value"}
    }


def test_log_and_error(caplog):
    log.setLevel(logging.ERROR)
    msg = "Something bad happened"
    with raises(UWConfigError) as e:
        raise support.log_and_error(msg)
    assert msg in str(e.value)
    assert logged(caplog, msg)


def test_walk_key_path_fail_bad_key_path():
    with raises(UWError) as e:
        support.walk_key_path({"a": {"b": {"c": "cherry"}}}, ["a", "x"])
    assert str(e.value) == "Bad config path: a.x"


def test_walk_key_path_fail_bad_leaf_value():
    with raises(UWError) as e:
        support.walk_key_path({"a": {"b": {"c": "cherry"}}}, ["a", "b", "c"])
    assert str(e.value) == "Value at a.b.c must be a dictionary"


def test_walk_key_path_pass():
    expected = ({"c": "cherry"}, "a.b")
    assert support.walk_key_path({"a": {"b": {"c": "cherry"}}}, ["a", "b"]) == expected


def test_yaml_to_str(capsys):
    xs = " ".join("x" * 999)
    expected = f"xs: {xs}"
    cfgobj = YAMLConfig({"xs": xs})
    assert repr(cfgobj) == expected
    assert str(cfgobj) == expected
    cfgobj.dump()
    assert capsys.readouterr().out.strip() == expected


class Test_UWYAMLConvert:
    """
    Tests for class uwtools.config.support.UWYAMLConvert.
    """

    def comp(self, ts: support.UWYAMLConvert, s: str):
        assert yaml.dump(ts, default_flow_style=True).strip() == s

    @fixture
    def loader(self):
        yaml.add_representer(support.UWYAMLConvert, support.UWYAMLTag.represent)
        return yaml.SafeLoader("")

    # These tests bypass YAML parsing, constructing nodes with explicit string values. They then
    # demonstrate that those nodes' convert() methods return representations in type type specified
    # by the tag.

    def test_bool_bad(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!bool", value="foo"))
        with raises(KeyError):
            ts.convert()

    @mark.parametrize("value, expected", [("False", False), ("True", True)])
    def test_bool_values(self, expected, loader, value):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!bool", value=value))
        assert ts.convert() == expected

    def test_datetime_no(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!datetime", value="foo"))
        with raises(ValueError):
            ts.convert()

    def test_datetime_ok(self, loader):
        ts = support.UWYAMLConvert(
            loader, yaml.ScalarNode(tag="!datetime", value="2024-08-09 12:22:42")
        )
        assert ts.convert() == datetime(2024, 8, 9, 12, 22, 42)
        self.comp(ts, "!datetime '2024-08-09 12:22:42'")

    def test_float_no(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!float", value="foo"))
        with raises(ValueError):
            ts.convert()

    def test_float_ok(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!float", value="3.14"))
        assert ts.convert() == 3.14
        self.comp(ts, "!float '3.14'")

    def test_int_no(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!int", value="foo"))
        with raises(ValueError):
            ts.convert()

    def test_int_ok(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!int", value="42"))
        assert ts.convert() == 42
        self.comp(ts, "!int '42'")

    def test___repr__(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!int", value="42"))
        assert str(ts) == "!int 42"


class Test_UWYAMLRemove:
    """
    Tests for class uwtools.config.support.UWYAMLRemove.
    """

    def test___repr__(self):
        yaml.add_representer(support.UWYAMLRemove, support.UWYAMLTag.represent)
        node = support.UWYAMLRemove(yaml.SafeLoader(""), yaml.ScalarNode(tag="!remove", value=""))
        assert str(node) == "!remove"
