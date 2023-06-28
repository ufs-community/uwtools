"""
Tests for schema validation tool
"""

import io
import json
from contextlib import redirect_stdout

import jsonschema
import pytest
import yaml

from uwtools.test.support import fixture_posix


def test_validate_yaml_salad():
    """
    Test that simple salad schema is accepted as valid json schema and that it
    validates both valid and bad input files.
    """
    schema_fn = fixture_posix("schema/salad.jsonschema")
    input_fn = fixture_posix("fruit_config_similar.yaml")
    bad_input_fn = fixture_posix("bad_fruit_config.yaml")

    with open(schema_fn, "r", encoding="utf-8") as f:
        schema = json.load(f)
    with open(input_fn, encoding="utf-8") as f:
        infile = yaml.safe_load(f)
    outstring = io.StringIO()
    with redirect_stdout(outstring):
        jsonschema.validate(infile, schema)
    result = outstring.getvalue()
    assert result == ""
    with open(bad_input_fn, encoding="utf-8") as f:
        bad_infile = yaml.safe_load(f)
    with pytest.raises(jsonschema.exceptions.ValidationError):
        jsonschema.validate(bad_infile, schema)
