# pylint: disable=missing-function-docstring,redefined-outer-name

import os
from pathlib import Path
from unittest.mock import patch

from pytest import fixture, raises

from uwtools.api import template
from uwtools.exceptions import UWTemplateRenderError


@fixture
def kwargs():
    return {
        "input_file": "infile",
        "output_file": "outfile",
        "values_src": "valsfile",
        "values_format": "format",
        "overrides": {"key": "val"},
        "searchpath": None,
        "env": True,
        "values_needed": True,
        "dry_run": True,
    }


def test_render(kwargs):
    with patch.object(template, "_render") as _render:
        template.render(**kwargs)
    _render.assert_called_once_with(
        **{
            **kwargs,
            "input_file": Path(kwargs["input_file"]),
            "output_file": Path(kwargs["output_file"]),
            "values_src": Path(kwargs["values_src"]),
        }
    )


def test_render_fail(kwargs):
    with patch.object(template, "_render", return_value=None):
        with raises(UWTemplateRenderError):
            template.render(**kwargs)


def test_render_to_str(kwargs):
    del kwargs["output_file"]
    with patch.object(template, "render") as render:
        template.render_to_str(**kwargs)
        render.assert_called_once_with(**{**kwargs, "output_file": Path(os.devnull)})


def test_translate():
    kwargs: dict = {
        "input_file": "path1",
        "output_file": "path2",
        "dry_run": True,
    }
    with patch.object(template, "_convert_atparse_to_jinja2") as _catj:
        assert template.translate(**kwargs)
    _catj.assert_called_once_with(
        input_file=Path(kwargs["input_file"]),
        output_file=Path(kwargs["output_file"]),
        dry_run=kwargs["dry_run"],
    )
