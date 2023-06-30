"""
Tests for the atparse-to-jinja2 tool.
"""

from unittest.mock import patch

from tests.support import fixture_path
from uwtools.cli import atparse_to_jinja2


def test_main_to_file(tmp_path):
    """
    Test that all atparse @[] items are replaced with Jinja2 templates {{ }}
    when writing to file.
    """
    outfile = str(tmp_path / "out")
    argv = ["test", "-i", fixture_path("ww3_multi.inp.IN"), "--outfile", outfile]
    with patch.object(atparse_to_jinja2.sys, "argv", argv):
        atparse_to_jinja2.main()
    with open(outfile, "r", encoding="utf-8") as f:
        file_content = f.read()
    assert "@[" not in file_content


def test_main_to_stdout(capsys):
    """
    Test that all atparse @[] items are replaced with Jinja2 templates {{ }}
    when printing to stdout.
    """
    argv = ["test", "-i", fixture_path("ww3_multi.inp.IN"), "-d"]
    with patch.object(atparse_to_jinja2.sys, "argv", argv):
        atparse_to_jinja2.main()
    assert "@[" not in capsys.readouterr().out
