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


@pytest.mark.parametrize("val", (True, 3.14, 88, None))
def test_dereference_no_op(val):
    # These types of values pass through dereferencing unmodified:
    assert jinja2.dereference(val=val, context={}) == val


def test_dereference_str_expression_rejected():
    # Unrenderable expressions are reported and returned unmodified:
    val = "{% for a in as %}{{ a }}{% endfor %}"
    assert jinja2.dereference(val=val, context={}) == val


def test_dereference_str_expression_rendered():
    # Context permitting, Jinja2 expressions are rendered:
    assert (
        jinja2.dereference(
            val="{% for a in as %}{{ a }}{% endfor %}", context={"as": ["a", "b", "c"]}
        )
        == "abc"
    )


def test_dereference_str_filter_rendered():
    assert (
        jinja2.dereference(
            val="{{ ['hello', recipient] | join(', ') }}", context={"recipient": "world"}
        )
        == "hello, world"
    )


def test_dereference_str_variable_rejected():
    # Unrenderable variables are reported and returned unmodified:
    val = "{{ n }}"
    assert jinja2.dereference(val=val, context={}) == val


def test_dereference_str_variable_rendered_int():
    # Due to reification, the value of a result parsable as an int is an int. The same holds for
    # other results parsable by YAML as Python values, but this is only a representative, non-
    # exhaustive test.
    assert jinja2.dereference(val="{{ number }}", context={"number": "88"}) == 88


def test_derefrence_str_variable_rendered_mixed():
    # A mixed result remains a str.
    assert (
        jinja2.dereference(val="{{ n }} is an {{ t }}", context={"n": 88, "t": "int"})
        == "88 is an int"
    )


def test_dereference_str_variable_rendered_str():
    # A pure str result remains a str.
    assert jinja2.dereference(val="{{ greeting }}", context={"greeting": "hello"}) == "hello"


# def test_dereference():
#     """
#     Test that the Jinja2 fields are filled in as expected.
#     """
#     with patch.dict(os.environ, {"UFSEXEC": "/my/path/"}, clear=True):
#         with open(fixture_path("gfs.yaml"), "r", encoding="utf-8") as f:
#             val = yaml.safe_load(f)

#         jinja2.dereference(val, context={**os.environ, **val})

#         # Check that existing dicts remain:
#         assert isinstance(val["fcst"], dict)
#         assert isinstance(val["grid_stats"], dict)

#         # Check references to other items at same level, and order doesn't
#         # matter:
#         assert val["testupdate"] == "testpassed"

#         # Check references to other section items:
#         assert val["grid_stats"]["ref_fcst"] == 64

#         # Check environment values are included:
#         assert val["executable"] == "/my/path/"

#         # Check that env variables that are not defined do not change:
#         assert val["undefined_env"] == "{{ NOPE }}"

#         # Check undefined are left as-is:
#         assert val["datapath"] == "{{ [experiment_dir, current_cycle] | path_join }}"

#         # Check math:
#         assert val["grid_stats"]["total_points"] == 640000
#         assert val["grid_stats"]["total_ens_points"] == 19200000

#         # Check that statements expand:
#         assert val["fcst"]["output_hours"] == "0 3 6 9"

#         # Check that order isn't a problem:
#         assert val["grid_stats"]["points_per_level"] == 10000


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
