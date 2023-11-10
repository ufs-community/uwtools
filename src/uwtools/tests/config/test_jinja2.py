# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.utils.jinja2 module.
"""

import logging
import os
from types import SimpleNamespace as ns
from unittest.mock import patch

import pytest
import yaml
from jinja2 import DebugUndefined, Environment, UndefinedError
from pytest import fixture, raises

from uwtools.config import jinja2
from uwtools.config.jinja2 import J2Template
from uwtools.logging import log
from uwtools.tests.support import logged

# Fixtures


@fixture
def template(tmp_path):
    path = tmp_path / "template.jinja2"
    with open(path, "w", encoding="utf-8") as f:
        f.write("roses are {{roses}}, violets are {{violets}}")
    return str(path)


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


# Helpers


def render_helper(input_file, values_file, **kwargs):
    jinja2.render(
        input_file=input_file,
        values_file=values_file,
        **kwargs,
    )


def validate(template):
    assert template._values.get("greeting") == "Hello"
    assert template._values.get("recipient") == "the world"
    assert template.render() == "Hello to the world"
    assert template.undeclared_variables == {"greeting", "recipient"}


# Tests


@pytest.mark.parametrize("key", ["foo", "bar"])
def test_register_filters_path_join(key):
    s = "{{ ['dir', %s] | path_join }}" % key
    template = jinja2._register_filters(Environment(undefined=DebugUndefined)).from_string(s)
    context = {"foo": "subdir"}
    if key in context:
        template.render(**context)  # path_join filter succeeds
    else:
        with raises(UndefinedError):
            template.render(**context)  # path_join filter fails


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


class Test_Jinja2Template:
    """
    Tests for class uwtools.config.jinja2.Jinja2Template.
    """

    @fixture
    def testdata(self):
        return ns(
            config={"greeting": "Hello", "recipient": "the world"},
            template="{{greeting}} to {{recipient}}",
        )

    def test_bad_args(self, testdata):
        # It is an error to pass in neither a template path or a template string.
        with raises(RuntimeError):
            J2Template(testdata.config)

    def test_dump(self, testdata, tmp_path):
        path = tmp_path / "rendered.txt"
        j2template = J2Template(testdata.config, template_str=testdata.template)
        j2template.dump(output_path=path)
        with open(path, "r", encoding="utf-8") as f:
            assert f.read().strip() == "Hello to the world"

    def test_render_file(self, testdata, tmp_path):
        path = tmp_path / "template.jinja2"
        with path.open("w", encoding="utf-8") as f:
            print(testdata.template, file=f)
        validate(J2Template(testdata.config, template_path=path))

    def test_render_string(self, testdata):
        validate(J2Template(testdata.config, template_str=testdata.template))
