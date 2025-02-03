# pylint: disable=missing-function-docstring

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
