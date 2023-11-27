# pylint: disable=missing-function-docstring

from unittest.mock import patch

import pytest

from uwtools.api import config
from uwtools.utils.file import FORMAT


def test_compare():
    kwargs: dict = {
        "config_a_path": "path1",
        "config_a_format": "fmt1",
        "config_b_path": "path2",
        "config_b_format": "fmt2",
    }
    with patch.object(config, "_compare") as _compare:
        config.compare(**kwargs)
    _compare.assert_called_once_with(**kwargs)


def test_realize():
    kwargs: dict = {
        "input_file": "path1",
        "input_format": "fmt1",
        "output_file": "path2",
        "output_format": "fmt2",
        "values_file": "path3",
        "values_format": "fmt3",
        "values_needed": True,
        "dry_run": True,
    }
    with patch.object(config, "_realize") as _realize:
        config.realize(**kwargs)
    _realize.assert_called_once_with(**kwargs)


@pytest.mark.parametrize(
    "infmt,outfmt,success_expected",
    [
        (FORMAT.atparse, FORMAT.jinja2, True),
        ("invalid", FORMAT.jinja2, False),
        (FORMAT.atparse, "invalid", False),
    ],
)
def test_translate(infmt, outfmt, success_expected):
    kwargs: dict = {
        "input_file": "path1",
        "input_format": infmt,
        "output_file": "path2",
        "output_format": outfmt,
        "dry_run": True,
    }
    with patch.object(config, "_convert_atparse_to_jinja2") as _catj:
        assert config.translate(**kwargs) is success_expected
    if success_expected:
        _catj.assert_called_once_with(
            input_file=kwargs["input_file"],
            output_file=kwargs["output_file"],
            dry_run=kwargs["dry_run"],
        )


@pytest.mark.parametrize("infmt,success_expected", [(FORMAT.yaml, True), ("invalid", False)])
def test_validate(infmt, success_expected):
    kwargs: dict = {
        "input_file": "infile",
        "input_format": infmt,
        "schema_file": "schema",
    }
    with patch.object(config, "_validate", return_value=True) as _validate:
        assert config.validate(**kwargs) is success_expected
    if success_expected:
        _validate.assert_called_once_with(
            config_file=kwargs["input_file"], schema_file=kwargs["schema_file"]
        )
