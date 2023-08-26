# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.utils.templater module.
"""

import logging
import os
from unittest.mock import patch

import yaml
from pytest import fixture

from uwtools.config import templater
from uwtools.tests.support import logged


@fixture
def config_file(tmp_path):
    path = tmp_path / "config.yaml"
    yaml = """
roses: red
violets: blue
cannot:
    override: this
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(yaml)
    return str(path)


@fixture
def template(tmp_path):
    path = tmp_path / "template.jinja2"
    with open(path, "w", encoding="utf-8") as f:
        f.write("roses are {{roses}}, violets are {{violets}}")
    return str(path)


def render_helper(input_file, config_file, **kwargs):
    templater.render(
        input_file=input_file,
        config_file=config_file,
        **kwargs,
    )


def test_render(config_file, template, tmp_path):
    outfile = str(tmp_path / "out.txt")
    render_helper(input_file=template, config_file=config_file, output_file=outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read().strip() == "roses are red, violets are blue"


def test_render_dry_run(caplog, config_file, template):
    logging.getLogger().setLevel(logging.INFO)
    render_helper(
        input_file=template, config_file=config_file, output_file="/dev/null", dry_run=True
    )
    assert logged(caplog, "roses are red, violets are blue")


def test_render_values_missing(caplog, config_file, template):
    # Read in the config, remove the "roses" key, then re-write it.
    with open(config_file, "r", encoding="utf-8") as f:
        cfgobj = yaml.safe_load(f.read())
    del cfgobj["roses"]
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(yaml.dump(cfgobj))
    render_helper(input_file=template, config_file=config_file, output_file="/dev/null")
    assert logged(caplog, "Required value(s) not provided:")
    assert logged(caplog, "roses")


def test_render_values_needed(caplog, config_file, template):
    logging.getLogger().setLevel(logging.INFO)
    render_helper(
        input_file=template, config_file=config_file, output_file="/dev/null", values_needed=True
    )
    for var in ("roses", "violets"):
        assert logged(caplog, var)


def test__report(caplog):
    logging.getLogger().setLevel(logging.DEBUG)
    expected = """
Internal arguments:
---------------------------------------------------------------------
             foo: bar
longish_variable: 88
---------------------------------------------------------------------
""".strip()
    templater._report(dict(foo="bar", longish_variable=88))
    assert "\n".join(record.message for record in caplog.records) == expected


def test__set_up_config_obj_env():
    expected = {"roses": "white", "violets": "blue"}
    with patch.dict(os.environ, expected):
        actual = templater._set_up_config_obj()
    assert actual["roses"] == "white"
    assert actual["violets"] == "blue"


def test__set_up_config_obj_file(config_file):
    expected = {"roses": "white", "violets": "blue", "cannot": {"override": "this"}}
    actual = templater._set_up_config_obj(config_file=config_file, overrides={"roses": "white"})
    assert actual == expected
