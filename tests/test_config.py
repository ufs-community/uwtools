# pylint: disable=all
import pathlib
import pytest
import os

from solo.configuration import Configuration
from solo.template import Template, TemplateConstants

solo_file_base = pathlib.Path(os.path.join(os.path.dirname(__file__), '../src/jcsda-solo/src/tests/language'))
uwtools_file_base = os.path.join(os.path.dirname(__file__))


def test_configuration_no_schema():
    config = Configuration(os.path.join(solo_file_base, 'config.yaml'))
    assert len(config)

def test_configuration_with_schema_ok():
    config = Configuration(os.path.join(solo_file_base, 'config.yaml'), 'config_schema')
    assert len(config)

def test_configuation_parse_env():

    config = Configuration(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")),environment=True)

    expected = os.environ.get('HOME')
    actual = config.test_env
    assert actual == expected


def test_configuation_update():

    config = Configuration(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    config.add(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))

    expected =  "/home/myexpid/{{current_cycle}}"
    actual = config.datapath

    assert actual == expected


def test_configuation_update_object():

    config = Configuration(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    config2 = Configuration(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))
    config.add(data=config2)

    expected =  "/home/myexpid/{{current_cycle}}"
    actual = config.datapath

    assert actual == expected


def test_configuration_inplace_update():

    config = Configuration(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))

    expected =  "testpassed"
    actual = config.testupdate

    assert actual == expected

def test_configuration_realtime_update():

    config = Configuration(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    config.add(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))
    config = Template.substitute_structure( config, TemplateConstants.DOUBLE_CURLY_BRACES, config.get)

    expected =  "/home/myexpid/10102022"
    actual = config.updated_datapath

    assert actual == expected