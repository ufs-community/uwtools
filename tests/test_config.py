# pylint: disable=all

'''
test_config.py has a few of the inital functional tests for the extending a YAML configuration tool to include:
1. variable subsitution
2. ENV varirable strigification
3. A MOC include method to be implemented in PI5 as a YAML Tag !INCLUDE

NOTE: These are not to be intended as a representation of a final API user interface and
are packaged under the Configure Class for containment.
'''

import pathlib
import pytest
import os

from uwtools.configure import Configure
from uwtools.template import Template,TemplateConstants

uwtools_file_base = os.path.join(os.path.dirname(__file__))

def test_configuation_parse_env():
    '''A basic test to check for env variables with the designator ${KEY} are realized'''

    os.environ['TEST'] = 'TEST_TRUE'
    config = Configure(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))

    expected = os.environ.get('TEST')
    actual = config.test_env
    assert actual == expected

# A test to see the ${KEY} desginator is left untouched as $(KEY)
# is expanded from a key valule pair from a second YAML file.
# In the following PI5 this include method will be implemented as an !INCLUDE tag
def test_configuation_update():

    config = Configure(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    config.include(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))

    expected =  "/home/myexpid/{{current_cycle}}"
    actual = config.datapath

    assert actual == expected

# A similar test to see if a configure object (in this case a NiceDict Object) can also be updated
# Notice the optional argument designed by the keyword data is being tested here
def test_configuation_update_object():
    '''Test to see if a configure object can also be updated'''

    config = Configure(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    config2 = Configure(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))
    config.include(data=config2)

    expected =  "/home/myexpid/{{current_cycle}}"
    actual = config.datapath

    assert actual == expected

# A test that a $(KEY) designator can be expanded from a key value pair that is in the same file
def test_configuration_inplace_update():

    config = Configure(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))

    expected =  "testpassed"
    actual = config.testupdate

    assert actual == expected

# A test to check that the ${KEY} works this does not represent the user interface to souch a capablity
# this is a functional test that on how to use the Template Class for when this is implemented
# in the Confiuration Manger work to be for fully developed in PI5
def test_configuration_realtime_update():

    config = Configure(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    config.include(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))
    config = Template.substitute_structure( config, TemplateConstants.DOUBLE_CURLY_BRACES, config.get)

    expected =  "/home/myexpid/10102022"
    actual = config.updated_datapath

    assert actual == expected
