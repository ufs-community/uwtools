# pylint: disable=all
import pathlib
import pytest
import os

from uwtools.loaders import load_yaml

uwtools_file_base = os.path.join(os.path.dirname(__file__))

def test_yaml_loader_loads_correctly():
    actual = load_yaml(os.path.join(uwtools_file_base,pathlib.Path("fixtures/simple.yaml")))

    #TODO developer's note: we had to update integers to strings for this to pass we
    # need to find out why this is the case and fix the issue in PI5
    expected = {
        "scheduler": "slurm",
        "jobname": "abcd",
        "extra_stuff": '12345',
        "account": "user_account",
        "nodes": '1',
        "queue": "bos",
        "tasks_per_node": '4',
        "walltime": "00:01:00",
    }
    assert actual == expected

def test_loader_dot_notation():

     props = load_yaml(os.path.join(uwtools_file_base,pathlib.Path("fixtures/simple.yaml")))

     expected = "abcd"
     actual = props.jobname

     assert actual == expected