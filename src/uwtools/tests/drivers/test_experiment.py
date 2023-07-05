# pylint: disable=missing-function-docstring
"""
Tests for uwtools.drivers.experiment module
"""

from pytest import fixture

from uwtools.drivers import experiment


@fixture
def SRWExperiment():
    return experiment.SRWExperiment()

def test_SRWExperiment_load_config(SRWExperiment):
    
