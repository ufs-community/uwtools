# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.utils.jinja2 module.
"""

import logging
import os
from unittest.mock import patch

import yaml
from pytest import fixture

from uwtools.config import jinja2
from uwtools.logging import log
from uwtools.tests.support import logged


@fixture
def values_file(tmp_path):
    path = tmp_path / "values.yaml"
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


def render_helper(input_file, values_file, **kwargs):
    jinja2.render(
        input_file=input_file,
        values_file=values_file,
        **kwargs,
    )


def test_render(values_file, template, tmp_path):
    outfile = str(tmp_path / "out.txt")
    render_helper(input_file=template, values_file=values_file, output_file=outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read().strip() == "roses are red, violets are blue"


def test_render_dry_run(caplog, values_file, template):
    log.setLevel(logging.INFO)
    render_helper(
        input_file=template, values_file=values_file, output_file="/dev/null", dry_run=True
    )
    assert logged(caplog, "roses are red, violets are blue")


def test_render_values_missing(caplog, values_file, template):
    # Read in the config, remove the "roses" key, then re-write it.
    log.setLevel(logging.INFO)
    with open(values_file, "r", encoding="utf-8") as f:
        cfgobj = yaml.safe_load(f.read())
    del cfgobj["roses"]
    with open(values_file, "w", encoding="utf-8") as f:
        f.write(yaml.dump(cfgobj))
    render_helper(input_file=template, values_file=values_file, output_file="/dev/null")
    assert logged(caplog, "Required value(s) not provided:")
    assert logged(caplog, "roses")


def test_render_values_needed(caplog, values_file, template):
    log.setLevel(logging.INFO)
    render_helper(
        input_file=template, values_file=values_file, output_file="/dev/null", values_needed=True
    )
    for var in ("roses", "violets"):
        assert logged(caplog, var)


def test__report(caplog):
    log.setLevel(logging.DEBUG)
    expected = """
Internal arguments:
---------------------------------------------------------------------
             foo: bar
longish_variable: 88
---------------------------------------------------------------------
""".strip()
    jinja2._report(dict(foo="bar", longish_variable=88))
    assert "\n".join(record.message for record in caplog.records) == expected


def test__set_up_config_obj_env():
    expected = {"roses": "white", "violets": "blue"}
    with patch.dict(os.environ, expected, clear=True):
        actual = jinja2._set_up_values_obj()
    assert actual["roses"] == "white"
    assert actual["violets"] == "blue"


def test__set_up_config_obj_file(values_file):
    expected = {"roses": "white", "violets": "blue", "cannot": {"override": "this"}}
    actual = jinja2._set_up_values_obj(values_file=values_file, overrides={"roses": "white"})
    assert actual == expected
