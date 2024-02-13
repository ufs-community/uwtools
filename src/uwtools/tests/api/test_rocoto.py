# pylint: disable=missing-function-docstring

from pathlib import Path
from unittest.mock import patch

from uwtools.api import rocoto


def test_realize():
    with patch.object(rocoto, "_realize") as _realize:
        rocoto.realize(config=Path("foo"), output_file=Path("bar"))
    _realize.assert_called_once_with(config="foo", output_file="bar")


def test_validate():
    with patch.object(rocoto, "_validate") as _validate:
        rocoto.validate(xml_file=Path("foo"))
    _validate.assert_called_once_with(xml_file="foo")
