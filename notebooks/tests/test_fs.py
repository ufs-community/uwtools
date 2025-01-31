import os

import yaml
from testbook import testbook


def test_copy():
    # Get the config files as text and dictionaries.
    with open("fixtures/fs/copy-config.yaml", "r", encoding="utf-8") as f:
        config_str = f.read().rstrip()
        config_dict = yaml.safe_load(config_str)
    with open("fixtures/fs/copy-keys-config.yaml", "r", encoding="utf-8") as f:
        config_keys_str = f.read().rstrip()
        config_keys_dict = yaml.safe_load(config_keys_str)
    with testbook("fs.ipynb", execute=True) as tb:
        # Each key in each config should have created a copy of the file given by each value.
        for item in config_dict.items():
            with open("tmp/copy-target/" + item[0], "r", encoding="utf-8") as f:
                copy_dst_txt = f.read().rstrip()
            with open("tmp/copier-target/" + item[0], "r", encoding="utf-8") as f:
                copier_dst_txt = f.read().rstrip()
            with open(item[1], "r", encoding="utf-8") as f:
                src_txt = f.read().rstrip()
            assert copy_dst_txt == src_txt
            assert copier_dst_txt == src_txt
        for item in config_keys_dict["files"]["to"]["copy"].items():
            with open("tmp/copy-keys-target/" + item[0], "r", encoding="utf-8") as f:
                copy_keys_dst_txt = f.read().rstrip()
            with open(item[1], "r", encoding="utf-8") as f:
                src_txt = f.read().rstrip()
            assert copy_keys_dst_txt == src_txt
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


def test_link():
    # Get the config files as text and dictionaries.
    with open("fixtures/fs/link-config.yaml", "r", encoding="utf-8") as f:
        config_str = f.read().rstrip()
        config_dict = yaml.safe_load(config_str)
    with open("fixtures/fs/link-keys-config.yaml", "r", encoding="utf-8") as f:
        config_keys_str = f.read().rstrip()
        config_keys_dict = yaml.safe_load(config_keys_str)
    with testbook("fs.ipynb", execute=True) as tb:
        # Each key in each config should have created a symlink of the file given by each value.
        for item in config_dict.items():
            link_path = "tmp/link-target/" + item[0]
            linker_path = "tmp/linker-target/" + item[0]
            with open(link_path, "r", encoding="utf-8") as f:
                link_dst_txt = f.read().rstrip()
            with open(linker_path, "r", encoding="utf-8") as f:
                linker_dst_txt = f.read().rstrip()
            with open(item[1], "r", encoding="utf-8") as f:
                src_txt = f.read().rstrip()
            assert os.path.islink(link_path)
            assert link_dst_txt == src_txt
            assert os.path.islink(linker_path)
            assert linker_dst_txt == src_txt
        for item in config_keys_dict["files"]["to"]["link"].items():
            link_keys_path = "tmp/link-keys-target/" + item[0]
            with open(link_keys_path, "r", encoding="utf-8") as f:
                link_keys_dst_txt = f.read().rstrip()
            with open(item[1], "r", encoding="utf-8") as f:
                src_txt = f.read().rstrip()
            assert os.path.islink(link_keys_path)
            assert link_keys_dst_txt == src_txt
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


def test_makedirs():
    # Get the config files as text and dictionaries.
    with open("fixtures/fs/dir-config.yaml", "r", encoding="utf-8") as f:
        config_str = f.read().rstrip()
        config_dict = yaml.safe_load(config_str)
    with open("fixtures/fs/dir-keys-config.yaml", "r", encoding="utf-8") as f:
        config_keys_str = f.read().rstrip()
        config_keys_dict = yaml.safe_load(config_keys_str)
    with testbook("fs.ipynb", execute=True) as tb:
        # Each value in each config should have been created as one or more subdirectories.
        for subdir in config_dict["makedirs"]:
            assert os.path.exists("tmp/dir-target/" + subdir)
            assert os.path.exists("tmp/makedirs-target/" + subdir)
        for subdir in config_keys_dict["path"]["to"]["dirs"]["makedirs"]:
            assert os.path.exists("tmp/dir-keys-target/" + subdir)
        # Ensure that cell output text matches expectations.
        assert tb.cell_output_text(53) == config_str
        assert (
            "{'ready': ['tmp/dir-target/foo', 'tmp/dir-target/bar/baz'], 'not-ready': []}"
            in tb.cell_output_text(55)
        )
        assert tb.cell_output_text(59) == config_keys_str
        assert (
            "{'ready': ['tmp/dir-keys-target/foo/bar', 'tmp/dir-keys-target/baz'],"
            "\n 'not-ready': []}"
        ) in tb.cell_output_text(61)
