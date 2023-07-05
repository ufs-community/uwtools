"""
Tests for uwtools.validate_config module
"""
import logging

from pytest import raises

from uwtools import config_validator
from uwtools.tests.support import fixture_path


def test_validate_config_no_errors():
    """
    Test that a valid config file succeeds validation.
    """
    with raises(SystemExit) as e:
        config_validator.validate_config(
            config_file=fixture_path("schema_test_good.yaml"),
            validation_schema=fixture_path("schema/workflow.jsonschema"),
            log=logging.getLogger(),
        )
    assert e.value.code == 0


# def test_validate_config_with_errors():  # pylint: disable=unused-variable
#     """Make sure that errors cause system exit"""

#     validation_schema = os.path.join(
#         uwtools_file_base, pathlib.Path("../schema/workflow.jsonschema")
#     )

#     config_file = os.path.join(uwtools_file_base, pathlib.Path("fixtures/bad.yaml"))

#     args = ["-s", validation_schema, "-c", config_file]

#     with raises(SystemExit) as pytest_wrapped_e:
#         config_validator.validate_config(args)

#     assert pytest_wrapped_e.type == SystemExit
#     assert pytest_wrapped_e.value.code == "This configuration file has 7 errors"
