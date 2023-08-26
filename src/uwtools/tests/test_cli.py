# pylint: disable=missing-function-docstring

from uwtools import cli


def test_dict_from_key_eq_val_strings():
    assert not cli.dict_from_key_eq_val_strings([])
    assert cli.dict_from_key_eq_val_strings(["a=1", "b=2"]) == {"a": "1", "b": "2"}
