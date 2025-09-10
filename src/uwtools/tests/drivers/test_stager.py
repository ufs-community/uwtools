"""
Test methods in stager.
"""

from pathlib import Path
from unittest.mock import patch

from pytest import fixture, mark

from uwtools.api.config import get_yaml_config
from uwtools.drivers.stager import FileStager
from uwtools.utils import tasks


class NullDriver(FileStager):
    def __init__(self, config_file, rundir):
        config = get_yaml_config(config_file)
        config.dereference()
        self.config = config
        self.rundir = rundir

    def taskname(self, s):
        return f"Null {s}"


@fixture
def driver(tmp_path):
    i = tmp_path / "input"
    i.mkdir(parents=True, exist_ok=True)
    for fn in ["a.foo", "b.foo"]:
        (i / fn).touch()
    config = """
      tmp: %s
      files_to_copy:
        a.foo: '{{ tmp }}/input/a.foo'
        b.foo: '{{ tmp }}/input/b.foo'
      files_to_link:
        c.foo: '{{ tmp }}/input/a.foo'
        d.foo: '{{ tmp }}/input/a.foo'
        output/<files>: !glob '{{ tmp }}/input/*.foo'
      files_to_hardlink:
        e.foo: '{{ tmp }}/input/a.foo'
      """ % (tmp_path)
    cfg = tmp_path / "config.yaml"
    cfg.write_text(config)
    return NullDriver(config_file=cfg, rundir=tmp_path)


def test_files_to_copy(driver, tmp_path):
    driver.files_copied()
    assert (tmp_path / "a.foo").is_file()
    assert (tmp_path / "b.foo").is_file()


@mark.parametrize("success", [True, False])
def test_files_to_hardlink(driver, success, tmp_path):
    e = tmp_path / "e.foo"
    if success:
        driver.files_hardlinked()
        # It's a hardlink
        assert e.stat().st_nlink == 2
    else:
        with patch.object(tasks.os, "link", side_effect=OSError()):
            driver.files_hardlinked()
        # It's a copy
        assert e.stat().st_nlink == 1


def test_files_to_link(driver, tmp_path):
    driver.files_linked()
    for fn in ["c", "d", "output/a", "output/b"]:
        fp = Path(tmp_path / f"{fn}.foo")
        assert fp.is_symlink()
