# pylint: disable=all
import pathlib
import pytest
import os

from uwtools.loaders import load_yaml

from solo.configuration import Configuration
from solo.yaml_file import YAMLFile
from solo.template import Template, TemplateConstants

solo_file_base = os.path.join(os.path.dirname(__file__), '../src/jcsda-solo/src/tests/language')
uwtools_file_base = os.path.join(os.path.dirname(__file__))

def test_yaml_loader_loads_correctly():
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

     props = load_yaml(os.path.join(uwtools_file_base,pathlib.Path("fixtures/simple.yaml")))

     expected = "abcd"
     actual = props.jobname

     assert actual == expected


def test_configuration_no_schema():
    config = Configuration(os.path.join(solo_file_base, 'config.yaml'))
    assert len(config)


def test_configuration_with_schema_ok():
    config = Configuration(os.path.join(solo_file_base, 'config.yaml'), 'config_schema')
    assert len(config)

def test_YAML_loader_parse_env():

    props = Configuration(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")),environment=True)

    expected = os.environ.get('USER')
    actual = props.user
    assert actual == expected


def test_YAML_loader_update():

    props = Configuration(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    props2 = Configuration(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))

    config = Template.substitute_structure( props2, TemplateConstants.DOLLAR_PARENTHESES, props.get)

    expected =  "/home/myexpid/{{current_cycle}}"
    actual = config.datapath

    assert actual == expected

def test_YAML_loader_inplace_update():

    props = Configuration(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))
    config = Template.substitute_structure( props, TemplateConstants.DOLLAR_PARENTHESES, props.get)

    expected =  "testpassed"
    actual = props.testupdate

    assert actual == expected

def test_YAML_loader_realtime_update():

    props = Configuration(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    props2 = Configuration(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))
    config = Template.substitute_structure( props2, TemplateConstants.DOLLAR_PARENTHESES, props.get)
    config = Template.substitute_structure( config, TemplateConstants.DOUBLE_CURLY_BRACES, props.get)

    print(config)

    expected =  "/home/myexpid/10102022"
    actual = config.updated_datapath

    assert actual == expected