'''
Tests for schema validation tool
'''

# pylint: disable=wrong-import-position,wrong-import-order

import pytest
jsonschema = pytest.importorskip("jsonschema")

import io
import json
from contextlib import redirect_stdout
import os
import pathlib
import jsonschema # pylint: disable=import-error
import yaml


uwtools_file_base = os.path.join(os.path.dirname(__file__))

def test_validate_yaml_salad():     #pylint: disable=unused-variable
    '''
    Test that simple salad schema is accepted as valid json schema and that it validates both valid 
    and bad input files
    '''
    schema_file = os.path.join(os.path.dirname(uwtools_file_base), pathlib.Path("schema/salad.jsonschema"))
    input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/fruit_config_similar.yaml"))
    bad_input_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/bad_fruit_config.yaml"))

    with open(schema_file, 'r', encoding="utf-8") as schema_file:
        schema = json.load(schema_file)
        with open(input_file, encoding="utf-8") as input_file:
            infile = yaml.safe_load(input_file)
        outstring = io.StringIO()
        with redirect_stdout(outstring):
            jsonschema.validate(infile, schema)
        result = outstring.getvalue()
        assert result == ""

        with open(bad_input_file, encoding="utf-8") as bad_input_file:
            bad_infile = yaml.safe_load(bad_input_file)
        with pytest.raises(jsonschema.exceptions.ValidationError):
            jsonschema.validate(bad_infile, schema)
