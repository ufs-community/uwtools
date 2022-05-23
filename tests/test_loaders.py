# pylint: disable=all
import pathlib
import pytest

from uwtools.loaders import load_yaml


def test_yaml_loader_loads_correctly():
    actual = load_yaml(pathlib.Path("tests/fixtures/simple.yaml"))

    expected = {
        "scheduler": "slurm",
        "jobname": "abcd",
        "extra_stuff": 12345,
        "account": "user_account",
        "nodes": 1,
        "queue": "bos",
        "tasks_per_node": 4,
        "walltime": "00:01:00",
    }
    assert actual == expected


def test_loader_dot_notation():

    props = load_yaml(pathlib.Path("tests/fixtures/simple.yaml"))

    expected = "abcd"
    actual = props.jobname

    assert actual == expected


# test 1
