# pylint: disable=missing-function-docstring
"""
Tests for uwtools.logging module.
"""

import logging
import os
import sys
from unittest.mock import patch

from pytest import raises

import uwtools.logging

# NB: Since pytest takes control of logging, these tests make assertions about the way logging
# setup calls were made instead of obtaining the root Logger object and making assertions about
# it.

DATEFMT = "%Y-%m-%dT%H:%M:%S"
FMT = "[%(asctime)s] %(levelname)8s %(message)s"


def test_setup_logging():
    with patch.object(logging, "basicConfig") as basicConfig:
        uwtools.logging.setup_logging()
        basicConfig.assert_called_once_with(
            datefmt=DATEFMT,
            filename=None,
            format=FMT,
            level=logging.INFO,
            stream=sys.stderr,
        )


def test_setup_logging_quiet():
    with patch.object(logging, "basicConfig") as basicConfig:
        uwtools.logging.setup_logging(quiet=True)
        basicConfig.assert_called_once_with(
            datefmt=DATEFMT,
            filename=os.devnull,
            format=FMT,
            level=logging.INFO,
            stream=None,
        )


def test_setup_logging_quiet_and_verbose():
    with raises(SystemExit):
        uwtools.logging.setup_logging(quiet=True, verbose=True)


def test_setup_logging_verbose():
    with patch.object(logging, "basicConfig") as basicConfig:
        uwtools.logging.setup_logging(verbose=True)
        basicConfig.assert_called_once_with(
            datefmt=DATEFMT,
            filename=None,
            format=FMT,
            level=logging.DEBUG,
            stream=sys.stderr,
        )
