# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.drivers.experiment module.
"""

from pytest import fixture

from uwtools.drivers import experiment


@fixture
def SRWExperiment():
    return experiment.SRWExperiment()


def test_SRWExperiment_load_config(SRWExperiment):
    assert SRWExperiment
