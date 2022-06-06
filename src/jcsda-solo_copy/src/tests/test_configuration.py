import os
from solo.configuration import Configuration

"""
    Just testing the arguments to configuration. Language is tested elsewhere.
"""


file_base = os.path.join(os.path.dirname(__file__), 'language')


def test_configuration_no_schema():
    config = Configuration(os.path.join(file_base, 'config.yaml'), file_base)
    assert len(config)


def test_configuration_with_schema_ok():
    config = Configuration(os.path.join(file_base, 'config.yaml'), file_base, 'config_schema')
    assert len(config)
