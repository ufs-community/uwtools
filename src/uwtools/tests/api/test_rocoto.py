# pylint: disable=missing-function-docstring
import os
from unittest.mock import patch

from uwtools.api import rocoto


def test_realize():
    with patch.object(rocoto, "_realize") as _realize:
        rocoto.realize(input_file="foo", output_file="bar")
    _realize.assert_called_once_with(config="foo", output_file="bar")


def test_realizt_to_str():
    val = "an-xml-string"
    with patch.object(rocoto, "_realize", return_value=val) as _realize:
        assert rocoto.realizt_to_str(input_file="foo") == val
    _realize.assert_called_once_with(config="foo", output_file=os.devnull)


def test_validate():
    with patch.object(rocoto, "_validate") as _validate:
        rocoto.validate(input_file="foo")
    _validate.assert_called_once_with(xml_file="foo")
