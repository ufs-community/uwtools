"""
Set of tests for wrapping experiments with a facade
"""
# pylint: disable=undefined-variable, unused-variable, unused-argument, unused-import
import os

import pytest

uwtools_file_base = os.path.join(os.path.dirname(__file__))


@pytest.mark.skip(reason="no way of currently testing this")
def test_load_config():
    """Test that YAML load, update, and dump work with a basic YAML file."""


@pytest.mark.skip(reason="no way of currently testing this")
def test_validate_config():
    """Test that the YAML file is validated correctly."""


@pytest.mark.skip(reason="no way of currently testing this")
def test_create_experiment():
    """Test that the experiment directory and manager files are created."""


@pytest.mark.skip(reason="no way of currently testing this")
def test_create_manager():
    """Test that the manager files are created."""


@pytest.mark.skip(reason="no way of currently testing this")
def test_link_fix_files():
    """Test that the fix files are linked."""
