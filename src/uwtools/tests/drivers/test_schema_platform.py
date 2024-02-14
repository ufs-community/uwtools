# pylint: disable=missing-function-docstring
"""
Tests for the "platform" schema.
"""

from uwtools.tests.support import validator, with_del, with_set


def test_fv3_schema_platform():
    d = {"account": "me", "scheduler": "slurm"}
    errors = validator("platform.jsonschema", "properties", "platform")
    # Basic correctness:
    assert not errors(d)
    # Extra top-level keys are forbidden:
    assert "Additional properties are not allowed" in errors(with_set(d, "bar", "foo"))
    # There is a fixed set of supported schedulers:
    assert "'foo' is not one of ['lsf', 'pbs', 'slurm']" in errors(with_set(d, "foo", "scheduler"))
    # account and scheduler are optional:
    assert not errors({})
    # account is required if scheduler is specified:
    assert "'account' is a dependency of 'scheduler'" in errors(with_del(d, "account"))
    # scheduler is required if account is specified:
    assert "'scheduler' is a dependency of 'account'" in errors(with_del(d, "scheduler"))
