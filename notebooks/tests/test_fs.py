from glob import glob
from pathlib import Path

import yaml
from pytest import fixture
from testbook import testbook

base = Path("fixtures/fs/config")


@fixture(scope="module")
def tb():
    with testbook("fs.ipynb", execute=True) as tb:
        yield tb


def test_fs_copy(load, tb):
    # Get the config files as text and dictionaries.
    config_str = load(base / "copy.yaml")
    config_keys_str = load(base / "copy-keys.yaml")
    # Each key in each config should have created a copy of the file given by each value.
    for item in yaml.safe_load(config_str).items():
        src_txt = load(item[1])
        assert load(f"tmp/copy-target/{item[0]}") == src_txt
        assert load(f"tmp/copier-target/{item[0]}") == src_txt
    for item in yaml.safe_load(config_keys_str)["files"]["to"]["copy"].items():
        src_txt = load(item[1])
        assert load(f"tmp/copy-keys-target/{item[0]}") == src_txt
    # Ensure that cell output text matches expectations.
    assert tb.cell_output_text(5) == config_str
    assert (
        "{'ready': ['tmp/copy-target/file1-copy.nml',"
        "\n  'tmp/copy-target/data/file2-copy.txt',"
        "\n  'tmp/copy-target/data/file3-copy.csv'],"
        "\n 'not-ready': []}" in tb.cell_output_text(7)
    )
    assert (
        "{'ready': [], 'not-ready': ['tmp/copy-target/missing-copy.nml']}"
        in tb.cell_output_text(11)
    )
    assert tb.cell_output_text(13) == tb.cell_output_text(9)
    assert tb.cell_output_text(15) == config_keys_str
    assert (
        "{'ready': ['tmp/copy-keys-target/file1-copy.nml',"
        "\n  'tmp/copy-keys-target/data/file2-copy.txt',"
        "\n  'tmp/copy-keys-target/data/file3-copy.csv'],"
        "\n 'not-ready': []}" in tb.cell_output_text(17)
    )


def test_fs_link(load, tb):
    # Get the config files as text and dictionaries.
    config_str = load(base / "link.yaml")
    config_keys_str = load(base / "link-keys.yaml")
    # Each key in each config should have created a symlink of the file given by each value.
    for item in yaml.safe_load(config_str).items():
        link_path = Path("tmp/link-target/", item[0])
        linker_path = Path("tmp/linker-target/", item[0])
        src_txt = load(item[1])
        assert link_path.is_symlink()
        assert load(link_path) == src_txt
        assert linker_path.is_symlink()
        assert load(linker_path) == src_txt
    for item in yaml.safe_load(config_keys_str)["files"]["to"]["link"].items():
        link_keys_path = Path("tmp/link-keys-target/", item[0])
        src_txt = load(item[1])
        assert link_keys_path.is_symlink()
        assert load(link_keys_path) == src_txt
    # Ensure that cell output text matches expectations.
    assert tb.cell_output_text(29) == config_str
    assert (
        "{'ready': ['tmp/link-target/file1-link.nml',"
        "\n  'tmp/link-target/file2-link.txt',"
        "\n  'tmp/link-target/data/file3-link.csv'],"
        "\n 'not-ready': []}"
    ) in tb.cell_output_text(31)
    assert (
        "{'ready': [], 'not-ready': ['tmp/link-target/missing-link.nml']}"
        in tb.cell_output_text(35)
    )
    assert tb.cell_output_text(37) == tb.cell_output_text(33)
    assert tb.cell_output_text(39) == config_keys_str
    assert (
        "{'ready': ['tmp/link-keys-target/file1-link.nml',"
        "\n  'tmp/link-keys-target/file2-link.txt',"
        "\n  'tmp/link-keys-target/data/file3-link.csv'],"
        "\n 'not-ready': []}"
    ) in tb.cell_output_text(41)


def test_fs_makedirs(load, tb):
    # Get the config files as text and dictionaries.
    config_str = load(base / "dir.yaml")
    config_keys_str = load(base / "dir-keys.yaml")
    # Each value in each config should have been created as one or more subdirectories.
    for subdir in yaml.safe_load(config_str)["makedirs"]:
        assert Path("tmp/dir-target/", subdir).exists()
        assert Path("tmp/makedirs-target/", subdir).exists()
    for subdir in yaml.safe_load(config_keys_str)["path"]["to"]["dirs"]["makedirs"]:
        assert Path("tmp/dir-keys-target/", subdir).exists()
    # Ensure that cell output text matches expectations.
    assert tb.cell_output_text(53) == config_str
    assert (
        "{'ready': ['tmp/dir-target/foo', 'tmp/dir-target/bar/baz'], 'not-ready': []}"
        in tb.cell_output_text(55)
    )
    assert tb.cell_output_text(59) == config_keys_str
    assert (
        "{'ready': ['tmp/dir-keys-target/foo/bar', 'tmp/dir-keys-target/baz'],\n 'not-ready': []}"
    ) in tb.cell_output_text(61)


def test_fs_glob_copy_basic(load, report, tb):
    d = Path("tmp/glob-copy")
    expected = {d / x for x in ("file1.nml", "file2.txt", "file3.csv")}
    for p in expected:
        assert p.is_file()
    assert {Path(x) for x in glob(f"{d}/*")} == expected
    assert tb.cell_output_text(73) == load(base / "glob-copy.yaml")
    r = report(74)
    assert {*r["ready"]} == set(map(str, expected))
    assert not r["not-ready"]


def test_fs_glob_copy_recursive(load, report, tb):
    d = Path("tmp/glob-copy-recursive")
    expected = {d / x for x in ("file1.nml", "subdir1/file4.nml", "subdir2/file5.nml")}
    for p in expected:
        assert p.is_file()
    assert {Path(x) for x in glob(f"{d}/**/*", recursive=True) if Path(x).is_file()} == expected
    assert tb.cell_output_text(78) == load(base / "glob-copy-recursive.yaml")
    r = report(79)
    assert {*r["ready"]} == set(map(str, expected))
    assert not r["not-ready"]


def test_fs_glob_copy_ignore_dirs(load, report, tb):
    d = Path("tmp/glob-copy-ignore-dirs")
    assert not d.is_dir()
    assert tb.cell_output_text(83) == load(base / "glob-copy-ignore-dirs.yaml")
    r = report(84)
    assert not r["ready"]
    assert not r["not-ready"]


def test_fs_glob_link_recursive(load, report, tb):
    d = Path("tmp/glob-link-recursive")
    expected = {d / x for x in ("file1.nml", "subdir1/file4.nml", "subdir2/file5.nml")}
    for p in expected:
        assert p.is_symlink()
    assert {Path(x) for x in glob(f"{d}/**/*", recursive=True) if Path(x).is_file()} == expected
    assert tb.cell_output_text(86) == load(base / "glob-link-recursive.yaml")
    r = report(87)
    assert {*r["ready"]} == set(map(str, expected))
    assert not r["not-ready"]


def test_fs_glob_link_link_dirs(load, report, tb):
    d = Path("tmp/glob-link-dirs")
    expected = {d / x for x in ("subdir1", "subdir2")}
    for p in expected:
        assert p.is_symlink()
    assert {Path(x) for x in glob(f"{d}/*")} == expected
    assert tb.cell_output_text(90) == load(base / "glob-link-dirs.yaml")
    r = report(91)
    assert {*r["ready"]} == set(map(str, expected))
    assert not r["not-ready"]


def test_fs_copy_http(load, report, tb):
    d = Path("tmp/licenses")
    expected = d / "gpl"
    assert expected.is_file()
    assert glob(f"{d}/*") == [str(expected)]
    assert tb.cell_output_text(94) == load(base / "copy-http.yaml")
    r = report(95)
    assert r["ready"] == [str(expected)]
    assert not r["not-ready"]


# Helpers


@fixture
def report(tb):
    def report(cell: int) -> dict:
        lines = tb.cell_output_text(cell).split("\n")
        stdout = "\n".join([line for line in lines if not line.startswith("[")])
        return yaml.safe_load(stdout)

    return report
