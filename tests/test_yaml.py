'''
test_config.py are the initial unit tests for the extending a YAML configuration tool:
1. variable substitution
2. ENV variable strigification
3. A MOC include method to be implemented in PI5 as a YAML Tag !INCLUDE

NOTE: The generic YAML parsing tests using the Template Class  are not to be intended as a
representation of a final user interface and are packaged under the Configure Class for containment
'''

#pylint: disable=unused-variable
import os
import pathlib

from uwtools.yaml_file import YAMLFile

uwtools_file_base = os.path.join(os.path.dirname(__file__))

def test_yaml_parse_env():
    '''A basic test to check for env variables with the designator ${KEY} are realized'''

    os.environ['TEST'] = 'TEST_TRUE'
    yaml_config = YAMLFile(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))

    expected = os.environ.get('TEST')
    actual = yaml_config.test_env
    assert actual == expected

def test_yaml_parse_env_no_var_present():
    '''Tests case when no environment variable is present and KEY designator is preserved'''
    yaml_config = YAMLFile(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))

    expected = "${TEST_NOCHANGE}"
    actual = yaml_config.test_noenv
    assert actual == expected


# A test to see the ${KEY} designator is left untouched as $(KEY)
# is expanded from a key value pair from a second YAML file.
# In the following PI5 this include method will be implemented as an !INCLUDE tag
def test_yaml_update():
    '''A test to see the ${KEY} designator is left untouched as $(KEY)'''

    yaml_config = YAMLFile(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    yaml_config.include(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))

    expected =  "/home/myexpid/{{current_cycle}}"
    actual = yaml_config.datapath

    assert actual == expected

# A similar test to see if a configure object (in this case a NiceDict Object) can also be updated
# Notice the optional argument designed by the keyword data is being tested here
def test_yaml_update_object():
    '''Test to see if a configure object can also be updated'''

    yaml_config = YAMLFile(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    yaml_config2 = YAMLFile(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))
    yaml_config.include(data=yaml_config2)

    expected =  "/home/myexpid/{{current_cycle}}"
    actual = yaml_config.datapath

    assert actual == expected

def test_configuration_inplace_update():
    '''A test the $(KEY) designator is expanded from a key value pair that is in the same file'''

    yaml_config = YAMLFile(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/gfs.yaml")))

    expected =  "testpassed"
    actual = yaml_config.testupdate

    assert actual == expected

def test_configuration_realtime_update():
    '''A test to check that the {{KEY}} works'''

    yaml_config = YAMLFile(pathlib.Path(os.path.join(uwtools_file_base,"fixtures/experiment.yaml")))
    yaml_config.include(pathlib.Path(
                        os.path.join(uwtools_file_base,"fixtures/gfs.yaml")),replace_realtime=True)

    expected =  "/home/myexpid/10102022"
    actual = yaml_config.updated_datapath

    assert actual == expected
