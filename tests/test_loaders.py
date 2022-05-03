# pylint: disable=all
import pathlib
import pytest

from uwtools.loaders import load_yaml


def test_yaml_loader_loads_correctly():
    actual = load_yaml(pathlib.Path("tests/fixtures/simple.yaml"))

    expected = {"scheduler": "slurm", "job_name": "abcd", "extra_stuff": 12345}
    assert actual == expected


def test_loader_dot_notation():

    props = load_yaml(pathlib.Path("tests/fixtures/simple.yaml"))

    expected = "abcd"
    actual = props.job_name

    assert actual == expected