# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.utils.atparse_to_jinja2 module.
"""
from io import StringIO
from unittest.mock import patch

from pytest import fixture

from uwtools.config import atparse_to_jinja2

# Helper functions


@fixture
def atparselines():
    return ["@[greeting] to the @[subject]", "@[flowers] are @[color]"]


@fixture
def atparsefile(atparselines, tmp_path):
    path = tmp_path / "atparse"
    with open(path, "w", encoding="utf-8") as f:
        for line in atparselines:
            print(line, file=f)
    return path


@fixture
def jinja2txt():
    return "{{greeting}} to the {{subject}}\n{{flowers}} are {{color}}\n"


# Test functions


def test_convert_input_file_to_output_file(atparsefile, capsys, jinja2txt, tmp_path):
    outfile = tmp_path / "outfile"
    atparse_to_jinja2.convert(input_file=atparsefile, output_file=outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read() == jinja2txt
    streams = capsys.readouterr()
    assert not streams.err
    assert not streams.out


def test_convert_input_file_to_stderr(atparsefile, capsys, jinja2txt, tmp_path):
    outfile = tmp_path / "outfile"
    atparse_to_jinja2.convert(input_file=atparsefile, dry_run=True)
    streams = capsys.readouterr()
    assert streams.err == jinja2txt
    assert not streams.out
    assert not outfile.is_file()


def test_convert_input_file_to_stdout(atparsefile, capsys, jinja2txt):
    atparse_to_jinja2.convert(input_file=atparsefile)
    streams = capsys.readouterr()
    assert not streams.err
    assert streams.out == jinja2txt


def test_convert_stdin_to_file(atparselines, capsys, jinja2txt, tmp_path):
    outfile = tmp_path / "outfile"
    with patch.object(atparse_to_jinja2.sys, "stdin", new=StringIO("\n".join(atparselines))):
        atparse_to_jinja2.convert(output_file=outfile)
    with open(outfile, "r", encoding="utf-8") as f:
        assert f.read() == jinja2txt
    streams = capsys.readouterr()
    assert not streams.err
    assert not streams.out


def test_convert_stdin_to_stderr(atparselines, capsys, jinja2txt, tmp_path):
    outfile = tmp_path / "outfile"
    with patch.object(atparse_to_jinja2.sys, "stdin", new=StringIO("\n".join(atparselines))):
        atparse_to_jinja2.convert(output_file=outfile, dry_run=True)
    assert capsys.readouterr().err == jinja2txt
    assert not outfile.is_file()


def test_convert_stdin_to_stdout(atparselines, capsys, jinja2txt):
    with patch.object(atparse_to_jinja2.sys, "stdin", new=StringIO("\n".join(atparselines))):
        atparse_to_jinja2.convert()
    streams = capsys.readouterr()
    assert not streams.err
    assert streams.out == jinja2txt


def test__replace():
    # A line without atparse syntax should be returned unchanged:
    line_without = "Hello to the world"
    assert atparse_to_jinja2._replace(line_without) == line_without
    # A line with atparse syntax should be returned updated to Jinja2 syntax:
    line_with = "@[greeting] to the @[subject]"
    assert atparse_to_jinja2._replace(line_with) == "{{greeting}} to the {{subject}}"
