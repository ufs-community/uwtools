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


def test_translate():
    kwargs: dict = {
        "input_file": "path1",
        "output_file": "path2",
        "dry_run": True,
    }
    with patch.object(template, "_convert_atparse_to_jinja2") as _catj:
        assert template.translate(**kwargs)
    _catj.assert_called_once_with(
        input_file=kwargs["input_file"],
        output_file=kwargs["output_file"],
        dry_run=kwargs["dry_run"],
    )
