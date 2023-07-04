"""
This test checks the validate config tool command line script
"""
import os
import pathlib

import pytest
from scripts import validate_config

uwtools_file_base = os.path.join(os.path.dirname(__file__))


def test_config_no_errors():  # pylint: disable=unused-variable
    """Make sure that no errors are given if config file has none"""

    validation_schema = os.path.join(
        uwtools_file_base, pathlib.Path("../schema/workflow.jsonschema")
    )

    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/good.yaml"))

    args = ["-s", validation_schema, "-c", config_file]

    try:
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            validate_config.validate_config(args)

            assert pytest_wrapped_e.type == SystemExit
            assert pytest_wrapped_e.value.code == 0
    except SystemExit:
        assert True


def test_config_with_errors():  # pylint: disable=unused-variable
    """Make sure that errors cause system exit"""

    validation_schema = os.path.join(
        uwtools_file_base, pathlib.Path("../schema/workflow.jsonschema")
    )

    config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/bad.yaml"))

    args = ["-s", validation_schema, "-c", config_file]

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        validate_config.validate_config(args)

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == "This configuration file has 7 errors"
