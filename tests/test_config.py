# pylint: disable=all
import pathlib
import pytest
import os

from uwtools.configure import Configure
from uwtools.template import Template,TemplateConstants

uwtools_file_base = os.path.join(os.path.dirname(__file__))

def test_configuation_parse_env():

    os.environ['TEST'] = 'TEST_TRUE'
    config = Configure(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))

    expected = os.environ.get('TEST')
    actual = config.test_env
    assert actual == expected


def test_configuation_update():

    config = Configure(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    config.include(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))

    expected =  "/home/myexpid/{{current_cycle}}"
    actual = config.datapath

    assert actual == expected


def test_configuation_update_object():

    config = Configure(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    config2 = Configure(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))
    config.include(data=config2)

    expected =  "/home/myexpid/{{current_cycle}}"
    actual = config.datapath

    assert actual == expected


def test_configuration_inplace_update():

    config = Configure(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))

    expected =  "testpassed"
    actual = config.testupdate

    assert actual == expected

def test_configuration_realtime_update():

    config = Configure(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    config.include(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))
    config = Template.substitute_structure( config, TemplateConstants.DOUBLE_CURLY_BRACES, config.get)

    expected =  "/home/myexpid/10102022"
    actual = config.updated_datapath

    assert actual == expected