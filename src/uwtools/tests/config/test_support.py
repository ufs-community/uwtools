# pylint: disable=missing-function-docstring,protected-access
"""
Tests for uwtools.config.jinja2 module.
"""

import logging
from collections import OrderedDict

import f90nml  # type: ignore
import pytest
import yaml
from pytest import fixture, raises

from uwtools.config import support
from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.config.formats.ini import INIConfig
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.sh import SHConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.tests.support import logged
from uwtools.utils.file import FORMAT


@pytest.mark.parametrize(
    "d,n", [({1: 88}, 1), ({1: {2: 88}}, 2), ({1: {2: {3: 88}}}, 3), ({1: {}}, 2)]
)
def test_depth(d, n):
    assert support.depth(d) == n


@pytest.mark.parametrize(
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


def test_log_and_error(caplog):
    log.setLevel(logging.ERROR)
    msg = "Something bad happened"
    with raises(UWConfigError) as e:
        raise support.log_and_error(msg)
    assert msg in str(e.value)
    assert logged(caplog, msg)


def test_represent_namelist():
    namelist = f90nml.reads("&namelist\n key = value\n/\n")
    assert yaml.dump(namelist, default_flow_style=True).strip() == "{namelist: {key: value}}"


def test_represent_ordereddict():
    ordereddict_values = OrderedDict([("example", OrderedDict([("key", "value")]))])
    assert (
        yaml.dump(ordereddict_values, default_flow_style=True).strip() == "{example: {key: value}}"
    )


class Test_TaggedString:
    """
    Tests for class uwtools.config.support.TaggedString.
    """

    def comp(self, ts: support.TaggedString, s: str):
        assert yaml.dump(ts, default_flow_style=True).strip() == s

    @fixture
    def loader(self):
        yaml.add_representer(support.TaggedString, support.TaggedString.represent)
        return YAMLConfig(config={})._yaml_loader

    # These tests bypass YAML parsing, constructing nodes with explicit string values. They then
    # demonstrate that those nodes' convert() methods return representations in type type specified
    # by the tag.

    def test_float_no(self, loader):
        ts = support.TaggedString(loader, yaml.ScalarNode(tag="!float", value="foo"))
        with raises(ValueError):
            ts.convert()

    def test_float_ok(self, loader):
        ts = support.TaggedString(loader, yaml.ScalarNode(tag="!float", value="3.14"))
        assert ts.convert() == 3.14
        self.comp(ts, "!float '3.14'")

    def test_int_no(self, loader):
        ts = support.TaggedString(loader, yaml.ScalarNode(tag="!int", value="foo"))
        with raises(ValueError):
            ts.convert()

    def test_int_ok(self, loader):
        ts = support.TaggedString(loader, yaml.ScalarNode(tag="!int", value="88"))
        assert ts.convert() == 88
        self.comp(ts, "!int '88'")

    def test___repr__(self, loader):
        ts = support.TaggedString(loader, yaml.ScalarNode(tag="!int", value="88"))
        assert str(ts) == "!int 88"
