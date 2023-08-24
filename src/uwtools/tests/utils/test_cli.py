# pylint: disable=missing-function-docstring
"""
Tests for uwtools.utils.cli module.
"""

from pytest import raises

from uwtools.utils import cli


def test_dict_from_key_eq_val_strings():
    assert not cli.dict_from_key_eq_val_strings([])
    assert cli.dict_from_key_eq_val_strings(["a=1", "b=2"]) == {"a": "1", "b": "2"}


def test_get_file_type():
    for ext, file_type in {
        "bash": "INI",
        "cfg": "INI",
        "ini": "INI",
        "nml": "NML",
        "sh": "INI",
        "yaml": "YAML",
        "yml": "YAML",
    }.items():
        assert cli.get_file_type(f"a.{ext}") == file_type


def test_path_if_it_exists(tmp_path):
    # Test non-existent path:
    path = tmp_path / "foo"
    with raises(FileNotFoundError):
        cli.path_if_it_exists(str(path))
    # Test directory that exists:
    assert cli.path_if_it_exists(str(tmp_path)) == str(tmp_path)
    # Test file that exists:
    path.touch()
    assert cli.path_if_it_exists(str(path)) == str(path)
