# pylint: disable=missing-function-docstring,protected-access
"""
Tests for uwtools.logging module.
"""

import logging
import os
from unittest.mock import ANY, patch

from pytest import raises

import uwtools.logging

# NB: Since pytest takes control of logging, these tests make assertions about the way logging
# setup calls were made instead of obtaining the root logger object and making assertions about
# it, since the root logger will not be what one would expect.


def test_setup_logging():
    with patch.object(logging, "basicConfig") as basicConfig:
        uwtools.logging.setup_logging()
        basicConfig.assert_called_once_with(
            datefmt=ANY,
            format=ANY,
            level=logging.INFO,
        )


def test_setup_logging_quiet():
    with patch.object(logging, "basicConfig") as basicConfig:
        uwtools.logging.setup_logging(quiet=True)
        basicConfig.assert_called_once_with(
            datefmt=ANY,
            filename=os.devnull,
            format=ANY,
            level=logging.INFO,
        )


def test_setup_logging_quiet_and_verbose():
    with raises(SystemExit):
        uwtools.logging.setup_logging(quiet=True, verbose=True)


def test_setup_logging_verbose():
    with patch.object(logging, "basicConfig") as basicConfig:
        uwtools.logging.setup_logging(verbose=True)
        basicConfig.assert_called_once_with(
            datefmt=ANY,
            format=ANY,
            level=logging.DEBUG,
        )


def test_use_logger():
    with patch.object(uwtools.logging, "log", uwtools.logging._Logger()):
        with patch.object(uwtools.logging.iotaa, "logset") as logset:
            # Initially, uwtools logging uses the Python root logger:
            assert uwtools.logging.log.logger == logging.getLogger()
            # But the logger can be swapped to use a logger of choice:
            test_logger = logging.getLogger("test-logger")
            uwtools.logging.use_logger(test_logger)
            assert uwtools.logging.log.logger == test_logger
            logset.assert_called_once_with(test_logger)
