# pylint: disable=duplicate-code,missing-function-docstring
"""
Tests for the atparse-to-jinja2 CLI.
"""

from types import SimpleNamespace as ns
from unittest.mock import patch

import pytest
from pytest import raises

from uwtools.cli import atparse_to_jinja2
from uwtools.tests.support import fixture_path

# NB: Ensure that at least one test exercises both short and long forms of each
#     CLI switch.


@pytest.mark.parametrize("sw", [ns(i="-i"), ns(i="--input-template")])
def test_main_bad_args(sw, capsys):
    argv = ["test", sw.i, fixture_path("ww3_multi.inp.IN")]
    with patch.object(atparse_to_jinja2.sys, "argv", argv):
        with raises(SystemExit) as e:
            atparse_to_jinja2.main()
        assert e.value.code == 1
        assert "Specify either --dry-run or --outfile" in capsys.readouterr().err


@pytest.mark.parametrize("sw", [ns(i="-i", o="-o"), ns(i="--input-template", o="--outfile")])
def test_main_to_file(sw, tmp_path):
    """
    Test that all atparse @[] items are replaced with Jinja2 templates {{ }} when writing to file.
    """
    outfile = str(tmp_path / "out")
    argv = ["test", sw.i, fixture_path("ww3_multi.inp.IN"), sw.o, outfile]
    with patch.object(atparse_to_jinja2.sys, "argv", argv):
        atparse_to_jinja2.main()
    with open(outfile, "r", encoding="utf-8") as f:
        file_content = f.read()
    assert "@[" not in file_content


@pytest.mark.parametrize("sw", [ns(d="-d", i="-i"), ns(d="--dry-run", i="--input-template")])
def test_main_to_stdout(sw, capsys):
    """
    Test that all atparse @[] items are replaced with Jinja2 templates {{ }} when printing to
    stdout.
    """
    argv = ["test", sw.i, fixture_path("ww3_multi.inp.IN"), sw.d]
    with patch.object(atparse_to_jinja2.sys, "argv", argv):
        atparse_to_jinja2.main()
    assert "@[" not in capsys.readouterr().out
