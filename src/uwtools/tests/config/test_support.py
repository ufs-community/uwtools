# pylint: disable=missing-function-docstring
"""
Tests for uwtools.config.jinja2 module.
"""

import configparser
import logging

import pytest
from pytest import raises

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


def test_config_sections():
    cfg = configparser.ConfigParser()
    sections = support.config_sections(cfg)
    cfg.read_string("[top]\n")
    assert not dict(sections.get("top"))


@pytest.mark.parametrize("d,n", [({1: 88}, 1), ({1: {2: 88}}, 2), ({1: {2: {3: 88}}}, 3)])
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
