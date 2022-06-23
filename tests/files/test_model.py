#pylint: disable=invalid-name, missing-module-docstring, missing-function-docstring
import pytest
from uwtools.files import Unix


def test_Unix():
    _file = Unix("file://tests/fixtures/files/a.txt")

    assert str(_file) == "file://tests/fixtures/files/a.txt"
    assert repr(_file) == "<Unix file://tests/fixtures/files/a.txt/>"


def test_Unix_validation():

    with pytest.raises(AttributeError) as error:
        Unix("ile://tests/fixtures/files/a.txt")

    assert "attribute unknown: [ile://]" in str(error)

    with pytest.raises(AttributeError) as error:
        Unix("//tests/fixtures/files/a.txt")

    assert "prefix not found in: [//tests/fixtures/files/a.txt]" in str(error)

    with pytest.raises(FileNotFoundError) as error:
        Unix("file://ests/fixtures/files/a.txt")

    assert "File not found [file://ests/fixtures/files/a.txt]" in str(error)
