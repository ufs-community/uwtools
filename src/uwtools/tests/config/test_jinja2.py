# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.jinja2 module.
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
from uwtools.config.support import TaggedString
from uwtools.logging import log
from uwtools.tests.support import logged, regex_logged

# Fixtures


@fixture
def deref_render_assets():
    log.setLevel(logging.DEBUG)
    return "{{ greeting + ' ' + recipient }}", {"greeting": "hello"}, {"recipient": "world"}


@fixture
def template(tmp_path):
    path = tmp_path / "template.jinja2"
    with open(path, "w", encoding="utf-8") as f:
        f.write("roses are {{roses_color}}, violets are {{violets_color}}")
    return str(path)


@fixture
def values_file(tmp_path):
    path = tmp_path / "values.yaml"
    yaml = """
roses_color: red
violets_color: blue
cannot:
    override: this
""".strip()
    with open(path, "w", encoding="utf-8") as f:
        f.write(yaml)
    return str(path)


# Helpers


def render_helper(input_file, values_file, **kwargs):
    jinja2.render(
        input_file=input_file,
        values=values_file,
        **kwargs,
    )


def validate(template):
    assert template._values.get("greeting") == "Hello"
    assert template._values.get("recipient") == "the world"
    assert template.render() == "Hello to the world"
    assert template.undeclared_variables == {"greeting", "recipient"}


# Tests


def test_dereference_key_expression():
    assert jinja2.dereference(val={"{{ fruit }}": "red"}, context={"fruit": "apple"}) == {
        "apple": "red"
    }


def test_dereference_local_values():
    # Rendering can use values from the local contents of the enclosing dict, but are shadowed by
    # values from the top-level context object.
    val = {
        "color": "blue",
        "apple": {
            "color": "red",
            "description": "A {{ color }} apple",  # top-level "color" will be used
        },
        "banana": {
            "description": "A banana, {{ state }}",  # local "state" will be used
            "state": "unpeeled",
        },
    }
    assert jinja2.dereference(val=val, context=val) == {
        "color": "blue",
        "apple": {"color": "red", "description": "A blue apple"},
        "banana": {"description": "A banana, unpeeled", "state": "unpeeled"},
    }


@pytest.mark.parametrize("val", (True, 3.14, 88, None))
def test_dereference_no_op(val):
    # These types of values pass through dereferencing unmodified:
    assert jinja2.dereference(val=val, context={}) == val


@pytest.mark.parametrize(
    "logmsg,val",
    [
        ("can only concatenate", "{{ 'str' + 11 }}"),
        ("'n' is undefined", "{{ n }}"),
        ("'as' is undefined", "{% for a in as %}{{ a }}{% endfor %}"),
        ("division by zero", "{{ 1 / 0 }}"),
    ],
)
def test_dereference_no_op_due_to_error(caplog, logmsg, val):
    # Erroneous inputs cause:
    #   - A type error due to + operating on a str and an int.
    #   - An undefined error due to reference to a non-existent value.
    #   - An undefined error in a loop expression.
    #   - A division-by-zero error.
    # The unrenderable expression is returned unmodified.
    log.setLevel(logging.DEBUG)
    assert jinja2.dereference(val=val, context={})
    assert regex_logged(caplog, logmsg)


def test_dereference_str_expression_rendered():
    # Context permitting, Jinja2 expressions are rendered:
    val = "{% for a in as %}{{ a }}{% endfor %}"
    assert jinja2.dereference(val=val, context={"as": ["a", "b", "c"]}) == "abc"


def test_dereference_str_filter_rendered():
    val = "{{ ['hello', recipient] | join(', ') }}"
    assert jinja2.dereference(val=val, context={"recipient": "world"}) == "hello, world"


def test_derefrence_str_variable_rendered_mixed():
    # A mixed result remains a str.
    val = "{{ n }} is an {{ t }}"
    assert jinja2.dereference(val=val, context={"n": 88, "t": "int"}) == "88 is an int"


def test_dereference_str_variable_rendered_str():
    # A pure str result remains a str.
    val = "{{ greeting }}"
    assert jinja2.dereference(val=val, context={"greeting": "hello"}) == "hello"


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


def test_render_calls__dry_run(template, tmp_path, values_file):
    outfile = str(tmp_path / "out.txt")
    with patch.object(jinja2, "_dry_run_template") as dr:
        render_helper(
            input_file=template, values_file=values_file, output_file=outfile, dry_run=True
        )
        dr.assert_called_once_with("roses are red, violets are blue")


def test_render_calls__log_missing(template, tmp_path, values_file):
    outfile = str(tmp_path / "out.txt")
    with open(values_file, "r", encoding="utf-8") as f:
        cfgobj = yaml.safe_load(f.read())
    del cfgobj["roses_color"]
    with open(values_file, "w", encoding="utf-8") as f:
        f.write(yaml.dump(cfgobj))

    with patch.object(jinja2, "_log_missing_values") as lmv:
        render_helper(
            input_file=template, values_file=values_file, output_file=outfile, dry_run=True
        )
        lmv.assert_called_once_with(["roses_color"])


def test_render_calls__values_needed(template, tmp_path, values_file):
    outfile = str(tmp_path / "out.txt")
    with patch.object(jinja2, "_values_needed") as vn:
        render_helper(
            input_file=template, values_file=values_file, output_file=outfile, values_needed=True
        )
        vn.assert_called_once_with({"roses_color", "violets_color"})


def test_render_calls__write(template, tmp_path, values_file):
    outfile = str(tmp_path / "out.txt")
    with patch.object(jinja2, "_write_template") as write:
        render_helper(input_file=template, values_file=values_file, output_file=outfile)
        write.assert_called_once_with(outfile, "roses are red, violets are blue")


def test_render_dry_run(caplog, template, values_file):
    log.setLevel(logging.INFO)
    render_helper(
        input_file=template, values_file=values_file, output_file="/dev/null", dry_run=True
    )
    assert logged(caplog, "roses are red, violets are blue")


def test_render_values_missing(caplog, template, values_file):
    # Read in the config, remove the "roses" key, then re-write it.
    log.setLevel(logging.INFO)
    with open(values_file, "r", encoding="utf-8") as f:
        cfgobj = yaml.safe_load(f.read())
    del cfgobj["roses_color"]
    with open(values_file, "w", encoding="utf-8") as f:
        f.write(yaml.dump(cfgobj))
    render_helper(input_file=template, values_file=values_file, output_file="/dev/null")
    assert logged(caplog, "Required value(s) not provided:")
    assert logged(caplog, "roses_color")


def test_render_values_needed(caplog, template, values_file):
    log.setLevel(logging.INFO)
    render_helper(
        input_file=template, values_file=values_file, output_file="/dev/null", values_needed=True
    )
    for var in ("roses_color", "violets_color"):
        assert logged(caplog, var)


@pytest.mark.parametrize("tag", ["!float", "!int"])
def test__deref_convert_no(caplog, tag):
    log.setLevel(logging.DEBUG)
    loader = yaml.SafeLoader(os.devnull)
    val = TaggedString(loader, yaml.ScalarNode(tag=tag, value="foo"))
    assert jinja2._deref_convert(val=val) == val
    assert not regex_logged(caplog, "Converted")
    assert regex_logged(caplog, "Conversion failed")


@pytest.mark.parametrize("converted,tag,value", [(3.14, "!float", "3.14"), (88, "!int", "88")])
def test__deref_convert_ok(caplog, converted, tag, value):
    log.setLevel(logging.DEBUG)
    loader = yaml.SafeLoader(os.devnull)
    val = TaggedString(loader, yaml.ScalarNode(tag=tag, value=value))
    assert jinja2._deref_convert(val=val) == converted
    assert regex_logged(caplog, "Converted")
    assert not regex_logged(caplog, "Conversion failed")


def test__deref_debug(caplog):
    log.setLevel(logging.DEBUG)
    jinja2._deref_debug(action="Frobnicated", val="foo")
    assert logged(caplog, "[dereference] Frobnicated: foo")


def test__deref_render_no(caplog, deref_render_assets):
    val, context, _ = deref_render_assets
    assert jinja2._deref_render(val=val, context=context) == val
    assert not regex_logged(caplog, "Rendered")
    assert regex_logged(caplog, "Rendering failed")


def test__deref_render_ok(caplog, deref_render_assets):
    val, context, local = deref_render_assets
    assert jinja2._deref_render(val=val, context=context, local=local) == "hello world"
    assert regex_logged(caplog, "Rendered")
    assert not regex_logged(caplog, "Rendering failed")


def test__dry_run_template(caplog):
    jinja2._dry_run_template("roses are red\nviolets are blue")
    assert logged(caplog, "roses are red")
    assert logged(caplog, "violets are blue")


def test__log_missing_values(caplog):
    missing = ["roses_color", "violets_color"]
    result = jinja2._log_missing_values(missing)
    assert result is False
    assert logged(caplog, "Required value(s) not provided:")
    assert logged(caplog, "roses_color")
    assert logged(caplog, "violets_color")


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
    expected = {"roses_color": "white", "violets_color": "blue"}
    with patch.dict(os.environ, expected, clear=True):
        actual = jinja2._set_up_values_obj()
    assert actual["roses_color"] == "white"
    assert actual["violets_color"] == "blue"


def test__set_up_config_obj_file(values_file):
    expected = {"roses_color": "white", "violets_color": "blue", "cannot": {"override": "this"}}
    actual = jinja2._set_up_values_obj(values_file=values_file, overrides={"roses_color": "white"})
    assert actual == expected


def test__values_needed(caplog):
    undeclared_variables = {"roses_color", "lavender_smell"}
    result = jinja2._values_needed(undeclared_variables)
    assert result is True
    assert logged(caplog, "Value(s) needed to render this template are:")
    assert logged(caplog, "roses_color")
    assert logged(caplog, "lavender_smell")


def test__write_template_to_file(tmp_path):
    outfile = str(tmp_path / "out.txt")
    jinja2._write_template(outfile, "roses are red, violets are blue")
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read().strip() == "roses are red, violets are blue"


def test__write_template_stdout(capsys):
    jinja2._write_template(None, "roses are red, violets are blue")
    actual = capsys.readouterr().out
    expected = "roses are red, violets are blue"
    assert actual.strip() == expected


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

    def test_dump(self, testdata, tmp_path):
        path = tmp_path / "rendered.txt"
        j2template = J2Template(values=testdata.config, template_source=testdata.template)
        j2template.dump(output_path=path)
        with open(path, "r", encoding="utf-8") as f:
            assert f.read().strip() == "Hello to the world"

    def test_render_file(self, testdata, tmp_path):
        path = tmp_path / "template.jinja2"
        with path.open("w", encoding="utf-8") as f:
            print(testdata.template, file=f)
        validate(J2Template(values=testdata.config, template_source=path))

    def test_render_string(self, testdata):
        validate(J2Template(values=testdata.config, template_source=testdata.template))
