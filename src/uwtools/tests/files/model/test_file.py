# pylint: disable=missing-function-docstring

from glob import glob

from pytest import raises

from uwtools.files import S3, Unix
from uwtools.tests.support import fixture_path, fixture_uri


def test_dir_file():
    """
    Tests dir method given a file.
    """
    suffix = "files/a.txt"
    my_init = Unix(fixture_uri(suffix))
    assert my_init.dir == glob(fixture_path(suffix))


def test_dir_path():
    """
    Tests dir method given a path, i.e. not a file.
    """
    my_init = Unix(fixture_uri())
    assert my_init.dir == glob(fixture_path("*"))


def test_S3():
    uri = "s3://foo/bar/files/a.txt"
    obj = S3(uri)
    assert obj.exists
    assert obj.path == "foo/bar/files/a.txt"
    assert str(obj).startswith("s3://")
    assert str(obj).endswith("files/a.txt")
    assert repr(obj).startswith("<S3 s3://")
    assert repr(obj).endswith("files/a.txt/>")
    assert not obj.dir


def test_Unix():
    uri = fixture_uri("files/a.txt")
    obj = Unix(uri)
    assert obj.exists
    assert obj.path == uri.replace("file://", "")
    assert str(obj).startswith("file://")
    assert str(obj).endswith("files/a.txt")
    assert repr(obj).startswith("<Unix file://")
    assert repr(obj).endswith("files/a.txt/>")


def test_Unix_bad_file(tmp_path):
    with raises(FileNotFoundError):
        Unix(uri=(tmp_path / "no-such-file").as_uri())


def test_Unix_bad_path_type():
    with raises(TypeError):
        Unix(uri=None)  # type: ignore


def test_Unix_bad_prefixes():
    with raises(ValueError):
        Unix(uri="foo:///bad/prefix")
    with raises(ValueError):
        Unix(uri="/no/prefix/at/all")
