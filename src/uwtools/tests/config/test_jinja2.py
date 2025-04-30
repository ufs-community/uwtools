"""
Tests for uwtools.config.jinja2 module.
"""

import os
from datetime import datetime, timezone
from io import StringIO
from textwrap import dedent
from types import SimpleNamespace as ns
from unittest.mock import patch

import yaml
from jinja2 import DebugUndefined, Environment, TemplateNotFound, UndefinedError
from pytest import fixture, mark, raises

from uwtools.config import jinja2
from uwtools.config.jinja2 import J2Template
from uwtools.config.support import UWYAMLConvert, UWYAMLRemove, uw_yaml_loader

# Fixtures


@fixture
def deref_render_assets():
    return "{{ greeting + ' ' + recipient }}", {"greeting": "hello"}, {"recipient": "world"}


@fixture
def supplemental_values(tmp_path):
    d = {"foo": "bar", "another": "value"}
    valsfile = tmp_path / "values.yaml"
    valsfile.write_text(yaml.dump(d))
    return ns(d=d, e={"CYCLE": "2024030112"}, f=valsfile, o={"baz": "qux"})


@fixture
def template_file(tmp_path):
    path = tmp_path / "template.jinja2"
    path.write_text("roses are {{roses_color}}, violets are {{violets_color}}")
    return path


@fixture
def values_file(tmp_path):
    path = tmp_path / "values.yaml"
    yaml = """
roses_color: red
violets_color: blue
cannot:
    override: this
""".strip()
    path.write_text(yaml)
    return path


# Helpers


def render_helper(input_file, values_file, **kwargs):
    return jinja2.render(
        input_file=input_file,
        values_src=values_file,
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


@mark.parametrize("val", [True, 3.14, 42, None])
def test_dereference_no_op(val):
    # These types of values pass through dereferencing unmodified:
    assert jinja2.dereference(val=val, context={}) == val


@mark.parametrize(
    ("logmsg", "val"),
    [
        ("can only concatenate", "{{ 'str' + 11 }}"),
        ("'n' is undefined", "{{ n }}"),
        ("'as' is undefined", "{% for a in as %}{{ a }}{% endfor %}"),
        ("division by zero", "{{ 1 / 0 }}"),
    ],
)
def test_dereference_no_op_due_to_error(logged, logmsg, val):
    # Erroneous inputs cause:
    #   - A type error due to + operating on a str and an int.
    #   - An undefined error due to reference to a non-existent value.
    #   - An undefined error in a loop expression.
    #   - A division-by-zero error.
    # The unrenderable expression is returned unmodified.
    assert jinja2.dereference(val=val, context={}) == val
    assert logged(logmsg)


def test_dereference_remove(logged):
    remove = UWYAMLRemove(yaml.SafeLoader(""), yaml.ScalarNode(tag="!remove", value=""))
    val = {"a": {"b": {"c": "cherry", "d": remove}}}
    assert jinja2.dereference(val=val, context={}) == {"a": {"b": {"c": "cherry"}}}
    assert logged("Removing value at: a.b.d")


def test_dereference_str_expression_rendered():
    # Context permitting, Jinja2 variables/expressions are rendered:
    val = "{% for a in as %}{{ a }}{% endfor %}"
    assert jinja2.dereference(val=val, context={"as": ["a", "b", "c"]}) == "abc"


def test_dereference_str_filter_rendered():
    val = "{{ ['hello', recipient] | join(', ') }}"
    assert jinja2.dereference(val=val, context={"recipient": "world"}) == "hello, world"


def test_dereference_str_variable_rendered_mixed():
    # A mixed result remains a str.
    val = "{{ n }} is an {{ t }}"
    assert jinja2.dereference(val=val, context={"n": 42, "t": "int"}) == "42 is an int"


def test_dereference_str_variable_rendered_str():
    # A pure str result remains a str.
    val = "{{ greeting }}"
    assert jinja2.dereference(val=val, context={"greeting": "hello"}) == "hello"


def test_deref_debug(logged):
    jinja2.deref_debug(action="Frobnicated", val="foo")
    assert logged("[dereference] Frobnicated: foo")


def test_register_filters_env():
    s = "hello {{ 'RECIPIENT' | env }}"
    template = jinja2._register_filters(Environment(undefined=DebugUndefined)).from_string(s)
    with patch.dict(os.environ, {"RECIPIENT": "world"}, clear=True):
        assert template.render() == "hello world"


@mark.parametrize("key", ["foo", "bar"])
def test_register_filters_path_join(key):
    s = "{{ ['dir', %s] | path_join }}" % key
    template = jinja2._register_filters(Environment(undefined=DebugUndefined)).from_string(s)
    context = {"foo": "subdir"}
    if key in context:
        template.render(**context)  # path_join filter succeeds
    else:
        with raises(UndefinedError):
            template.render(**context)  # path_join filter fails


def test_render(values_file, template_file, tmp_path):
    outfile = tmp_path / "out.txt"
    expected = "roses are red, violets are blue"
    result = render_helper(input_file=template_file, values_file=values_file, output_file=outfile)
    assert result == expected
    assert outfile.read_text().strip() == expected


def test_render_calls__dry_run(template_file, tmp_path, values_file):
    outfile = str(tmp_path / "out.txt")
    with patch.object(jinja2, "_dry_run_template") as dr:
        render_helper(
            input_file=template_file, values_file=values_file, output_file=outfile, dry_run=True
        )
        dr.assert_called_once_with("roses are red, violets are blue")


def test_render_calls__log_missing(template_file, tmp_path, values_file):
    outfile = str(tmp_path / "out.txt")
    cfgobj = yaml.safe_load(values_file.read_text())
    del cfgobj["roses_color"]
    values_file.write_text(yaml.dump(cfgobj))
    with patch.object(jinja2, "_log_missing_values") as lmv:
        render_helper(input_file=template_file, values_file=values_file, output_file=outfile)
        lmv.assert_called_once_with(["roses_color"])


def test_render_calls__values_needed(template_file, tmp_path, values_file):
    outfile = str(tmp_path / "out.txt")
    with patch.object(jinja2, "_values_needed") as vn:
        render_helper(
            input_file=template_file,
            values_file=values_file,
            output_file=outfile,
            values_needed=True,
        )
        vn.assert_called_once_with({"roses_color", "violets_color"})


def test_render_calls__write(template_file, tmp_path, values_file):
    outfile = str(tmp_path / "out.txt")
    with patch.object(jinja2, "_write_template") as write:
        render_helper(input_file=template_file, values_file=values_file, output_file=outfile)
        write.assert_called_once_with(outfile, "roses are red, violets are blue")


def test_render_dry_run(logged, template_file, values_file):
    expected = "roses are red, violets are blue"
    result = render_helper(input_file=template_file, values_file=values_file, dry_run=True)
    assert result == expected
    assert logged(expected)


def test_render_fails(logged, tmp_path):
    input_file = tmp_path / "template.yaml"
    input_file.write_text("{{ constants.pi }} {{ constants.e }}")
    values_file = tmp_path / "values.yaml"
    values_file.write_text("constants: {pi: 3.14}")
    assert render_helper(input_file=input_file, values_file=values_file) is None
    assert logged("Template render failed with error: 'dict object' has no attribute 'e'")


def test_render_values_missing(logged, template_file, values_file):
    # Read in the config, remove the "roses" key, then re-write it.
    cfgobj = yaml.safe_load(values_file.read_text())
    del cfgobj["roses_color"]
    values_file.write_text(yaml.dump(cfgobj))
    render_helper(input_file=template_file, values_file=values_file)
    assert logged("Value(s) required to render template not provided:")
    assert logged("  roses_color")


def test_render_values_needed(logged, template_file, values_file):
    render_helper(input_file=template_file, values_file=values_file, values_needed=True)
    for var in ("roses_color", "violets_color"):
        assert logged(f"  {var}")


@mark.parametrize(("s", "status"), [("foo: bar", False), ("foo: '{{ bar }} {{ baz }}'", True)])
def test_unrendered(s, status):
    assert jinja2.unrendered(s) is status


@mark.parametrize(
    ("tag", "value"),
    [
        ("!datetime", "foo"),
        ("!dict", "foo"),
        ("!float", "foo"),
        ("!int", "foo"),
        ("!list", "null"),
    ],
)
def test__deref_convert_no(logged, tag, value):
    loader = yaml.SafeLoader(os.devnull)
    val = UWYAMLConvert(loader, yaml.ScalarNode(tag=tag, value=value))
    assert jinja2._deref_convert(val=val) == val
    assert not logged("Converted")
    assert logged("Conversion failed")


@mark.parametrize(
    ("converted", "tag", "value"),
    [
        (True, "!bool", "True"),
        (False, "!bool", "0"),
        (
            datetime(2024, 9, 9, 0, 0, tzinfo=timezone.utc).replace(tzinfo=None),
            "!datetime",
            "2024-09-09 00:00:00",
        ),
        ({"a": 0, "b": 1}, "!dict", "{a: 0, b: 1}"),
        ({"a": 0, "b": 1}, "!dict", "[[a, 0], [b, 1]]"),
        (3.14, "!float", "3.14"),
        (42, "!int", "42"),
        ([0, 1, 2], "!list", "[0, 1, 2]"),
        (["f", "o", "o"], "!list", "foo"),
        ([0, 1, 2], "!list", "{0: a, 1: b, 2: c}"),
    ],
)
def test__deref_convert_ok(converted, logged, tag, value):
    loader = yaml.SafeLoader(os.devnull)
    val = UWYAMLConvert(loader, yaml.ScalarNode(tag=tag, value=value))
    assert jinja2._deref_convert(val=val) == converted
    assert logged("Converted")
    assert not logged("Conversion failed")


def test__deref_render_held(logged):
    val, context = "!int '{{ a }}'", yaml.load("a: !int '42'", Loader=uw_yaml_loader())
    assert jinja2._deref_render(val=val, context=context) == val
    assert logged("Rendered")
    assert logged("Held")


def test__deref_render_no(deref_render_assets, logged):
    val, context, _ = deref_render_assets
    assert jinja2._deref_render(val=val, context=context) == val
    assert not logged("Rendered")
    assert logged("Rendering failed")


def test__deref_render_ok(deref_render_assets, logged):
    val, context, local = deref_render_assets
    assert jinja2._deref_render(val=val, context=context, local=local) == "hello world"
    assert logged("Rendered")
    assert not logged("Rendering failed")


def test__deref_render_unloadable_val(logged):
    val = "&XMLENTITY;"
    assert jinja2._deref_render(val='{{ "%s" if True }}' % val, context={}) == val
    assert logged("Rendered")
    assert not logged("Rendering failed")


def test__dry_run_template(logged):
    jinja2._dry_run_template("roses are red\nviolets are blue")
    assert logged("roses are red")
    assert logged("violets are blue")


def test__log_missing_values(logged):
    missing = ["roses_color", "violets_color"]
    jinja2._log_missing_values(missing)
    assert logged("Value(s) required to render template not provided:")
    assert logged("  roses_color")
    assert logged("  violets_color")


def test__report(logged):
    expected = """
Internal arguments when rendering template:
---------------------------------------------------------------------
             foo: bar
longish_variable: 42
---------------------------------------------------------------------
""".strip()
    jinja2._report(dict(foo="bar", longish_variable=42))
    assert logged(expected, full=True)


def test__supplement_values():
    assert jinja2._supplement_values() == {}


def test__supplement_values_dict(supplemental_values):
    sv = supplemental_values
    assert jinja2._supplement_values(values_src=sv.d) == sv.d


def test__supplement_values_dict_plus_env(supplemental_values):
    sv = supplemental_values
    with patch.dict(os.environ, sv.e, clear=True):
        assert jinja2._supplement_values(values_src=sv.d, env=True) == {**sv.d, **sv.e}


def test__supplement_values_dict_plus_env_plus_overrides(supplemental_values):
    sv = supplemental_values
    with patch.dict(os.environ, sv.e, clear=True):
        assert jinja2._supplement_values(values_src=sv.d, env=True, overrides=sv.o) == {
            **sv.d,
            **sv.e,
            **sv.o,
        }


def test__supplement_values_dict_plus_overrides(supplemental_values):
    sv = supplemental_values
    assert jinja2._supplement_values(values_src=sv.d, overrides=sv.o) == {**sv.d, **sv.o}


def test__supplement_values_env(supplemental_values):
    sv = supplemental_values
    with patch.dict(os.environ, sv.e, clear=True):
        assert jinja2._supplement_values(env=True) == sv.e


def test__supplement_values_env_plus_overrides(supplemental_values):
    sv = supplemental_values
    with patch.dict(os.environ, sv.e, clear=True):
        assert jinja2._supplement_values(env=True, overrides=sv.o) == {**sv.o, **sv.e}


def test__supplement_values_overrides(supplemental_values):
    sv = supplemental_values
    assert jinja2._supplement_values(overrides=sv.o) == sv.o


def test__supplement_values_file(supplemental_values):
    sv = supplemental_values
    assert jinja2._supplement_values(values_src=sv.f) == sv.d


def test__supplement_values_file_plus_env(supplemental_values):
    sv = supplemental_values
    with patch.dict(os.environ, sv.e, clear=True):
        assert jinja2._supplement_values(values_src=sv.f, env=True) == {**sv.d, **sv.e}


def test__supplement_values_file_plus_env_plus_overrides(supplemental_values):
    sv = supplemental_values
    with patch.dict(os.environ, sv.e, clear=True):
        assert jinja2._supplement_values(values_src=sv.f, env=True, overrides=sv.o) == {
            **sv.d,
            **sv.e,
            **sv.o,
        }


def test__supplement_values_file_plus_overrides(supplemental_values):
    sv = supplemental_values
    assert jinja2._supplement_values(values_src=sv.d, overrides=sv.o) == {**sv.d, **sv.o}


def test__supplement_values_priority(supplemental_values):
    # Test environment variable > CLI key=value overrides > file value priority.
    sv = supplemental_values
    assert jinja2._supplement_values(values_src=sv.f)["foo"] == "bar"
    o = {"foo": "bar-cli"}
    assert jinja2._supplement_values(values_src=sv.f, overrides=o)["foo"] == o["foo"]
    e = {"foo": "bar-env"}
    with patch.dict(os.environ, e, clear=True):
        assert jinja2._supplement_values(values_src=sv.f, env=True, overrides=o)["foo"] == e["foo"]


def test__values_needed(logged):
    undeclared_variables = {"roses_color", "lavender_smell"}
    jinja2._values_needed(undeclared_variables)
    assert logged("Value(s) needed to render this template are:")
    assert logged("  roses_color")
    assert logged("  lavender_smell")


def test__write_template_to_file(tmp_path):
    outfile = tmp_path / "out.txt"
    jinja2._write_template(outfile, "roses are red, violets are blue")
    assert outfile.read_text().strip() == "roses are red, violets are blue"


def test__write_template_stdout(capsys):
    jinja2._write_template(None, "roses are red, violets are blue")
    actual = capsys.readouterr().out
    expected = "roses are red, violets are blue"
    assert actual.strip() == expected


class TestJ2Template:
    """
    Tests for class uwtools.config.jinja2.J2Template.
    """

    @fixture
    def searchpath_assets(self, tmp_path):
        def write(s, *args):
            path = tmp_path.joinpath(*list(args))
            path.parent.mkdir(exist_ok=True)
            path.write_text(s)
            return path

        write("{% macro double(x) %}{{ x }}{{ x }}{% endmacro %}", "m1.jinja")
        d1 = write("{% macro double(x) %}{{ x * 2 }}{% endmacro %}", "d1", "m1.jinja").parent
        d2 = write("{% macro triple(x) %}{{ x * 3 }}{% endmacro %}", "d2", "m2.jinja").parent
        s1 = """
        {% import 'm1.jinja' as m1 -%}
        {{ m1.double(1) }}
        """
        s1 = dedent(s1).strip()
        s2 = """
        {% import 'm1.jinja' as m1 -%}
        {% import 'm2.jinja' as m2 -%}
        {{ m1.double(1) }}{{ m2.triple(1) }}
        """
        s2 = dedent(s2).strip()
        t1 = write(s1, "t1.jinja")
        t2 = write(s2, "t2.jinja")
        return ns(d1=d1, d2=d2, s1=s1, s2=s2, t1=t1, t2=t2)

    @fixture
    def testdata(self):
        return ns(
            config={"greeting": "Hello", "recipient": "the world"},
            template="{{greeting}} to {{recipient}}",
        )

    def test_dump(self, testdata, tmp_path):
        path = tmp_path / "rendered.txt"
        obj = J2Template(values=testdata.config, template_source=testdata.template)
        obj.dump(output_path=path)
        assert path.read_text().strip() == "Hello to the world"

    def test_render_file(self, testdata, tmp_path):
        path = tmp_path / "template.jinja2"
        path.write_text(testdata.template)
        validate(J2Template(values=testdata.config, template_source=path))

    def test_render_string(self, testdata):
        validate(J2Template(values=testdata.config, template_source=testdata.template))

    def test_searchpath_file_default(self, searchpath_assets):
        # By default, the template search path will be the directory containing the main template:
        a = searchpath_assets
        assert J2Template(values={}, template_source=a.t1).render() == "11"

    def test_searchpath_file_one_path(self, searchpath_assets):
        # If a search path is specified, it will suppress use of the default path:
        a = searchpath_assets
        assert J2Template(values={}, template_source=a.t1, searchpath=[a.d1]).render() == "2"

    def test_searchpath_file_two_paths(self, searchpath_assets):
        # Multiple search paths can be specified:
        a = searchpath_assets
        result = J2Template(values={}, template_source=a.t2, searchpath=[a.d1, a.d2]).render()
        assert result == "23"

    def test_searchpath_stdin_default(self, searchpath_assets):
        # There is no default search path for reads from stdin:
        a = searchpath_assets
        with patch.object(jinja2, "readable") as readable, StringIO(a.s1) as sio:
            readable.return_value.__enter__.return_value = sio
            with raises(TemplateNotFound):
                J2Template(values={}).render()

    def test_searchpath_stdin_explicit(self, searchpath_assets):
        # An explicit search path is honored when reading from stdin:
        a = searchpath_assets
        with patch.object(jinja2, "readable") as readable, StringIO(a.s1) as sio:
            readable.return_value.__enter__.return_value = sio
            assert J2Template(values={}, searchpath=[a.d1]).render() == "2"

    def test_undeclared_variables(self):
        s = "{{ a }} {{ b.c }} {{ d.e.f[g] }} {{ h[i] }} {{ j[42] }} {{ k|default(l) }}"
        uvs = {"a", "b", "d", "g", "h", "i", "j", "k", "l"}
        assert J2Template(values={}, template_source=s).undeclared_variables == uvs

    def test__template_str(self, testdata):
        obj = J2Template(values=testdata.config, template_source=testdata.template)
        assert obj._template_str == "{{greeting}} to {{recipient}}"

    def test___repr__(self, testdata):
        obj = J2Template(values=testdata.config, template_source=testdata.template)
        assert str(obj) == "{{greeting}} to {{recipient}}"
