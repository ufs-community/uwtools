# pylint: disable=missing-function-docstring
"""
Tests for uwtools.logging module.
"""

import logging
import os
from unittest.mock import patch

from pytest import raises

import uwtools.logging

# NB: Since pytest takes control of logging, these tests make assertions about the way logging
# setup calls were made instead of obtaining the root logger object and making assertions about
# it, since the roog logger will not be what one would expect.

DATEFMT = "%Y-%m-%dT%H:%M:%S"
FMT = "[%(asctime)s] %(levelname)8s %(message)s"


def test_setup_logging():
    with patch.object(logging, "basicConfig") as basicConfig:
        uwtools.logging.setup_logging()
        basicConfig.assert_called_once_with(
            datefmt=DATEFMT,
            format=FMT,
            level=logging.INFO,
        )


def test_setup_logging_quiet():
    with patch.object(logging, "basicConfig") as basicConfig:
        uwtools.logging.setup_logging(quiet=True)
        basicConfig.assert_called_once_with(
            datefmt=DATEFMT,
            filename=os.devnull,
            format=FMT,
            level=logging.INFO,
        )


def test_setup_logging_quiet_and_verbose():
    with raises(SystemExit):
        uwtools.logging.setup_logging(quiet=True, verbose=True)


def test_setup_logging_verbose():
    with patch.object(logging, "basicConfig") as basicConfig:
        uwtools.logging.setup_logging(verbose=True)
        basicConfig.assert_called_once_with(
            datefmt=DATEFMT,
            format=FMT,
            level=logging.DEBUG,
        )
