# pylint: disable=missing-function-docstring

from glob import glob

from pytest import raises

from tests.support import fixture_path, fixture_uri
from uwtools.files import Unix
from uwtools.files.model import file


def test_dir_file():
    """Tests dir method given a file."""
    suffix = "files/a.txt"
    my_init = file.Unix(fixture_uri(suffix))
    assert my_init.dir == glob(fixture_path(suffix))


def test_dir_path():
    """Tests dir method given a path, i.e. not a file."""
    my_init = file.Unix(fixture_uri())
    assert my_init.dir == glob(fixture_path("*"))


def test_Unix():
    path = Unix(fixture_uri("files/a.txt"))
    assert path.exists
    assert str(path).startswith("file://")
    assert str(path).endswith("files/a.txt")
    assert repr(path).startswith("<Unix file://")
    assert repr(path).endswith("files/a.txt/>")


def test_Unix_validation():
    with raises(AttributeError) as error:
        Unix("ile://tests/fixtures/files/a.txt")
    assert "attribute unknown: [ile://]" in str(error)
    with raises(AttributeError) as error:
        Unix("//tests/fixtures/files/a.txt")
    assert "prefix not found in: [//tests/fixtures/files/a.txt]" in str(error)
    with raises(FileNotFoundError) as error:
        Unix("file://ests/fixtures/files/a.txt")
    assert "File not found [file://ests/fixtures/files/a.txt]" in str(error)
