# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.files.gateway.unix module.
"""

from pytest import fixture

from uwtools.files.gateway import unix
from uwtools.files.model.file import Unix


@fixture
def dirs(tmp_path):
    f1 = tmp_path / "src" / "f1"
    f2 = tmp_path / "src" / "subdir" / "f2"
    for path in f1, f2:
        path.parent.mkdir(parents=True)
        with open(path, "w", encoding="utf-8") as f:
            print(path.name, file=f)
    assert f1.is_file()
    assert f2.is_file()
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    return src, dst


@fixture
def files2copy(dirs):
    src, dst = dirs
    src1, src2 = [Unix(x.as_uri()) for x in (src / "f1", src / "subdir" / "f2")]
    dst1, dst2 = dst / "f1", dst / "f2"
    dst.mkdir()
    return src1, src2, dst1, dst2


def content(path):
    return [x.relative_to(path) for x in path.glob("**/*")]


def test_Copier_dir(dirs):
    src, dst = dirs
    assert not dst.is_dir()
    c = unix.Copier(srcs=[Unix(src.as_uri())], dsts=[dst])
    c.run()
    assert content(src) == content(dst)


def test_Copier_files(files2copy):
    src1, src2, dst1, dst2 = files2copy
    c = unix.Copier(srcs=[src1, src2], dsts=[dst1, dst2])
    assert not dst1.is_file()
    assert not dst2.is_file()
    c.run()
    assert dst1.is_file()
    assert dst2.is_file()


def test_copy_dir(dirs):
    src, dst = dirs
    assert not dst.is_dir()
    unix.copy(srcs=[Unix(src.as_uri())], dsts=[dst])
    assert content(src) == content(dst)


def test_copy_files(files2copy):
    src1, src2, dst1, dst2 = files2copy
    assert not dst1.is_file()
    assert not dst2.is_file()
    unix.copy(srcs=[src1, src2], dsts=[dst1, dst2])
    assert dst1.is_file()
    assert dst2.is_file()


def test__copy_dir_create(dirs):
    src, dst = dirs
    assert not dst.is_dir()
    unix._copy(src=src, dst=dst)
    assert content(src) == content(dst)


def test__copy_dir_replace(dirs):
    src, dst = dirs
    dst.mkdir()
    (dst / "junk").touch()
    unix._copy(src=src, dst=dst)
    assert content(src) == content(dst)  # i.e. junk is gone


def test__copy_file(dirs):
    src, dst = dirs
    srcfile, dstfile = src / "f1", dst / "f1"
    assert not dstfile.is_file()
    dst.mkdir()
    unix._copy(src=srcfile, dst=dstfile)
    assert dstfile.is_file()
