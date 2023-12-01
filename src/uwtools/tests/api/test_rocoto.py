# pylint: disable=missing-function-docstring

from unittest.mock import patch

from uwtools.api import rocoto


def test_realize():
    with patch.object(rocoto, "_realize") as _realize:
        rocoto.realize(input_file="foo", output_file="bar")
    _realize.assert_called_once_with(config_file="foo", output_file="bar")


def test_validate():
    with patch.object(rocoto, "_validate") as _validate:
        rocoto.validate(input_file="foo")
    _validate.assert_called_once_with(xml_file="foo")
