# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.utils.atparse_to_jinja2 module.
"""
from pytest import fixture, raises

from uwtools.utils import atparse_to_jinja2

# Helper functions


@fixture
def atparsefile(tmp_path):
    path = tmp_path / "atparse"
    with open(path, "w", encoding="utf-8") as f:
        for line in ["@[greeting] to the @[subject]", "@[flowers] are @[color]"]:
            print(line, file=f)
    return path


@fixture
def jinja2txt():
    return "{{greeting}} to the {{subject}}\n{{flowers}} are {{color}}\n"


# Test functions


def test_convert_bad_args():
    with raises(RuntimeError):
        atparse_to_jinja2.convert(input_template="/dev/null")


def test_convert_dry_run(atparsefile, capsys, jinja2txt):
    atparse_to_jinja2.convert(input_template=atparsefile, dry_run=True)
    assert capsys.readouterr().out == jinja2txt


def test_convert_outfile(atparsefile, jinja2txt, tmp_path):
    outfile = tmp_path / "outfile"
    atparse_to_jinja2.convert(input_template=atparsefile, outfile=outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read() == jinja2txt


def test__replace():
    # A line without atparse syntax should be returned unchanged:
    line_without = "Hello to the world"
    assert atparse_to_jinja2._replace(line_without) == line_without
    # A line with atparse syntax should be returned updated to Jinja2 syntax:
    line_with = "@[greeting] to the @[subject]"
    assert atparse_to_jinja2._replace(line_with) == "{{greeting}} to the {{subject}}"
