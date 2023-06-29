"""
Tests for the atparse_to_jinja2 tool.
"""

from unittest.mock import patch

from uwtools.cli import atparse_to_jinja2
from uwtools.test.support import fixture_path


def test_all_templates_replaced(capsys):
    """
    Test that all atparse @[] items are replaced with Jinja2 templates {{ }}.
    """
    argv = ["test", "-i", fixture_path("ww3_multi.inp.IN"), "-d"]
    with patch.object(atparse_to_jinja2.sys, "argv", argv):
        atparse_to_jinja2.main()
    assert "@[" not in capsys.readouterr().out
