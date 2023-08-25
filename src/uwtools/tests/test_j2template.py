# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.j2template module.
"""

from types import SimpleNamespace as ns

from pytest import fixture, raises

from uwtools.j2template import J2Template


@fixture
def testdata():
    return ns(
        config={"greeting": "Hello", "recipient": "the world"},
        template="{{greeting}} to {{recipient}}",
    )


def validate(template):
    assert template._configure_obj.get("greeting") == "Hello"
    assert template._configure_obj.get("recipient") == "the world"
    assert template.render_template() == "Hello to the world"
    assert template.undeclared_variables == {"greeting", "recipient"}


def test_bad_args(testdata):
    # It is an error to pass in neither a template path or a template string.
    with raises(RuntimeError):
        J2Template(testdata.config)


def test_dump_file(testdata, tmp_path):
    path = str(tmp_path / "rendered.txt")
    j2template = J2Template(testdata.config, template_str=testdata.template)
    j2template.dump_file(output_path=path)
    with open(path, "r", encoding="utf-8") as f:
        assert f.read().strip() == "Hello to the world"


def test_render_file(testdata, tmp_path):
    path = tmp_path / "template.jinja2"
    with path.open("w", encoding="utf-8") as f:
        print(testdata.template, file=f)
    validate(J2Template(testdata.config, template_path=str(path)))


def test_render_string(testdata):
    validate(J2Template(testdata.config, template_str=testdata.template))
