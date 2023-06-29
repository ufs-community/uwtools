# pylint: disable=missing-function-docstring,redefined-outer-name

"""
Unit tests for testing J2Template class
"""

from types import SimpleNamespace as ns

from pytest import fixture, raises

from uwtools.j2template import J2Template
from uwtools.test.support import fixture_path


@fixture
def testdata():
    return ns(
        config={"greeting": "Hello", "recipient": "the world"},
        message="Hello to the world",
        vars={"greeting", "recipient"},
    )


def test_render_string(testdata):
    # Render template from input string. Check that undeclared_variables returns
    # expected items.
    template = J2Template(testdata.config, template_str="{{greeting}} to {{recipient}}")
    assert template.configure_obj.get("greeting") == "Hello"
    assert template.configure_obj.get("recipient") == "the world"
    assert template.render_template() == testdata.message
    assert template.undeclared_variables == testdata.vars


def test_render_file(testdata):
    # Render template from input file. Check that undeclared_variables returns
    # expected items.
    template = J2Template(testdata.config, template_path=fixture_path("J2Template.IN"))
    assert template.configure_obj.get("greeting") == "Hello"
    assert template.configure_obj.get("recipient") == "the world"
    assert template.render_template() == testdata.message
    assert template.undeclared_variables == testdata.vars


def test_bad_args(testdata):
    # It is an error to pass in neither a template path or a template string.
    with raises(RuntimeError):
        J2Template(testdata.config)
