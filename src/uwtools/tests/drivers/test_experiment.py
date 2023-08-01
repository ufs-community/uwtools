# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.drivers.experiment module.
"""

import pytest

from uwtools.drivers import experiment
from uwtools.logger import Logger
from uwtools.tests.support import fixture_path


@pytest.fixture
def SRWExperiment():
    return experiment.SRWExperiment()


def test_SRWExperiment_load_config(SRWExperiment):
    assert SRWExperiment


@pytest.mark.skip(reason="no way of currently testing this")
def test_load_config():
    """
    Test that YAML load, update, and dump work with a basic YAML file.
    """


@pytest.mark.skip(reason="no way of currently testing this")
def test_validate_config(vals):
    """
    Test that a valid config file succeeds validation.
    """


@pytest.mark.skip(reason="no way of currently testing this")
def test_create_experiment():
    """
    Test that the experiment directory and manager files are created.
    """


@pytest.mark.skip(reason="no way of currently testing this")
def test_create_manager():
    """
    Test that the manager files are created.
    """


@pytest.mark.skip(reason="no way of currently testing this")
def test_link_fix_files():
    """
    Test that the fix files are linked.
    """
