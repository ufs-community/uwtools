"""
Test methods in stager.
"""

from pathlib import Path

from pytest import fixture

from uwtools.api.config import get_yaml_config
from uwtools.drivers.stager import FileStager

# Need one file on a non-/tmp disk for testing hardlink fallback
B_FILE = Path("./b.foo").resolve()


class NullDriver(FileStager):
    def __init__(self, config_file, rundir):
        config = get_yaml_config(config_file)
        config.dereference()
        self.config = config
        self.rundir = rundir

    def taskname(self, s):
        return f"Null {s}"


def setup_module(module):  # noqa: ARG001
    B_FILE.touch()


def teardown_module(module):  # noqa: ARG001
    B_FILE.unlink()


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
        b.foo: %s
      files_to_link:
        c.foo: '{{ tmp }}/input/a.foo'
        d.foo: '{{ tmp }}/input/a.foo'
        output/<files>: !glob '{{ tmp }}/input/*.foo'
      files_to_hardlink:
        e.foo: %s
        f.foo: '{{ tmp }}/input/a.foo'
      """ % (tmp_path, B_FILE, B_FILE)
    cfg = tmp_path / "config.yaml"
    cfg.write_text(config)
    return NullDriver(config_file=cfg, rundir=tmp_path)


def test_files_to_copy(driver, tmp_path):
    driver.files_copied()
    assert (tmp_path / "a.foo").is_file()
    assert (tmp_path / "b.foo").is_file()


def test_files_to_hardlink(driver, tmp_path):
    driver.files_hardlinked()
    a = tmp_path / "input" / "a.foo"
    e = tmp_path / "e.foo"
    f = tmp_path / "f.foo"
    assert e.is_file()
    assert not e.samefile(B_FILE)
    assert a.samefile(f)


def test_files_to_link(driver, tmp_path):
    driver.files_linked()
    for fn in ["c", "d", "output/a", "output/b"]:
        fp = Path(tmp_path / f"{fn}.foo")
        assert fp.is_symlink()
