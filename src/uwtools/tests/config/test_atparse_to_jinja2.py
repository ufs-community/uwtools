"""
Tests for uwtools.utils.atparse_to_jinja2 module.
"""

import sys
from io import StringIO
from unittest.mock import patch

from pytest import fixture

from uwtools.config import atparse_to_jinja2
from uwtools.utils.file import _stdinproxy

# Helper functions


@fixture
def txt_atparse():
    return """
@[greeting] to the @[subject]
@[flowers] are @[color]
""".strip()


@fixture
def txt_jinja2():
    return """
{{ greeting }} to the {{ subject }}
{{ flowers }} are {{ color }}
""".strip()


@fixture
def atparsefile(txt_atparse, tmp_path):
    path = tmp_path / "atparse.txt"
    path.write_text(txt_atparse)
    return path


# Test functions


def test_convert_input_file_to_output_file(atparsefile, capsys, txt_jinja2, tmp_path):
    outfile = tmp_path / "outfile"
    atparse_to_jinja2.convert(input_file=atparsefile, output_file=outfile)
    assert outfile.read_text().strip() == txt_jinja2
    streams = capsys.readouterr()
    assert not streams.err
    assert not streams.out


def test_convert_input_file_to_logging(atparsefile, capsys, logged, txt_jinja2, tmp_path):
    outfile = tmp_path / "outfile"
    atparse_to_jinja2.convert(input_file=atparsefile, dry_run=True)
    streams = capsys.readouterr()
    assert logged(txt_jinja2, full=True)
    assert not streams.out
    assert not outfile.is_file()


def test_convert_input_file_to_stdout(atparsefile, capsys, txt_jinja2):
    atparse_to_jinja2.convert(input_file=atparsefile)
    streams = capsys.readouterr()
    assert not streams.err
    assert streams.out.strip() == txt_jinja2


def test_convert_preserve_whitespace(tmp_path):
    atparse = """

@[first_entry]
  @[second_entry]
  @[third_entry]
    @[fourth_entry]

        @[fifth_entry] @[sixth_entry]

"""
    infile = tmp_path / "atparse"
    infile.write_text(atparse)
    outfile = tmp_path / "jinja2"
    atparse_to_jinja2.convert(input_file=infile, output_file=outfile)
    expected = """

{{ first_entry }}
  {{ second_entry }}
  {{ third_entry }}
    {{ fourth_entry }}

        {{ fifth_entry }} {{ sixth_entry }}

"""
    assert outfile.read_text() == expected


def test_convert_stdin_to_file(txt_atparse, capsys, txt_jinja2, tmp_path):
    outfile = tmp_path / "outfile"
    _stdinproxy.cache_clear()
    with StringIO(txt_atparse) as sio, patch.object(sys, "stdin", new=sio):
        atparse_to_jinja2.convert(output_file=outfile)
    assert outfile.read_text().strip() == txt_jinja2
    streams = capsys.readouterr()
    assert not streams.err
    assert not streams.out


def test_convert_stdin_to_logging(txt_atparse, logged, txt_jinja2, tmp_path):
    outfile = tmp_path / "outfile"
    _stdinproxy.cache_clear()
    with StringIO(txt_atparse) as sio, patch.object(sys, "stdin", new=sio):
        atparse_to_jinja2.convert(output_file=outfile, dry_run=True)
    assert logged(txt_jinja2, full=True)
    assert not outfile.is_file()


def test_convert_stdin_to_stdout(txt_atparse, capsys, txt_jinja2):
    _stdinproxy.cache_clear()
    with StringIO(txt_atparse) as sio, patch.object(sys, "stdin", new=sio):
        atparse_to_jinja2.convert()
    streams = capsys.readouterr()
    assert not streams.err
    assert streams.out.strip() == txt_jinja2


def test__replace():
    # A line without atparse syntax should be returned unchanged:
    line_without = "Hello to the world"
    assert atparse_to_jinja2._replace(line_without) == line_without
    # A line with atparse syntax should be returned updated to Jinja2 syntax:
    line_with = "@[greeting] to the @[subject]"
    assert atparse_to_jinja2._replace(line_with) == "{{ greeting }} to the {{ subject }}"
