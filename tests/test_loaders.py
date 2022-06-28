# pylint: disable=all
import pathlib
import pytest
import os

from uwtools.loaders import load_yaml

uwtools_file_base = os.path.join(os.path.dirname(__file__))

def test_yaml_loader_loads_correctly():
    '''Simple test to load a YAML file with basic value pairs of various types and check its results'''
    actual = load_yaml(os.path.join(uwtools_file_base,pathlib.Path("fixtures/simple.yaml")))

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
    '''Test to check the dot shortcut for resolving a dictionary element works in the response from YAML loader'''

     props = load_yaml(os.path.join(uwtools_file_base,pathlib.Path("fixtures/simple.yaml")))

     expected = "abcd"
     actual = props.jobname

     assert actual == expected
