# pylint: disable=missing-function-docstring

from unittest.mock import patch

from uwtools.api import template


def test_render():
    kwargs: dict = {
        "input_file": "infile",
        "output_file": "outfile",
        "values": "valsfile",
        "values_format": "format",
        "overrides": {"key": "val"},
        "values_needed": True,
        "dry_run": True,
    }
    with patch.object(template, "_render") as _render:
        template.render(**kwargs)
    _render.assert_called_once_with(**kwargs)
