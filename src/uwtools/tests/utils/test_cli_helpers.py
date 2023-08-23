# pylint: disable=missing-function-docstring
"""
Tests for uwtools.utils.cli_helpers module.
"""

from pytest import raises
from uwtools.utils import cli_helpers


def test_dict_from_key_eq_val_strings():
    assert not cli_helpers.dict_from_key_eq_val_strings([])
    assert cli_helpers.dict_from_key_eq_val_strings(["a=1", "b=2"]) == {"a": "1", "b": "2"}


def test_get_file_type():
    for ext, file_type in {
        "yaml": "YAML",
        "yml": "YAML",
        "bash": "INI",
        "sh": "INI",
        "ini": "INI",
        "cfg": "INI",
        "nml": "F90",
    }.items():
        assert cli_helpers.get_file_type(f"a.{ext}") == file_type


def test_path_if_it_exists(tmp_path):
    # Test non-existent path:
    path = tmp_path / "foo"
    with raises(FileNotFoundError):
        cli_helpers.path_if_it_exists(str(path))
    # Test directory that exists:
    assert cli_helpers.path_if_it_exists(str(tmp_path)) == str(tmp_path)
    # Test file that exists:
    path.touch()
    assert cli_helpers.path_if_it_exists(str(path)) == str(path)
