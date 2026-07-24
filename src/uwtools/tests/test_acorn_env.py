"""
Acorn (WCOSS2 test environment) smoke tests.

Run these on Acorn after loading the workflow environment:

    module use /path/to/uw-aigfs/modulefiles/
    module load wflow_wcoss

Then:

    python -m pytest src/uwtools/tests/test_acorn_env.py -v

These tests verify that the venv, uwtools version, and key dependencies
are functional before attempting a live workflow run on Acorn/WCOSS2.
"""

import importlib.metadata
import sys

import pytest


def test_python_version():
    """Python 3.12+ must be active — not the system Python 3.8.6 on WCOSS2."""
    major, minor = sys.version_info.major, sys.version_info.minor
    assert (major, minor) >= (3, 12), (
        f"Expected Python 3.12+, got {major}.{minor}. "
        "Check that wflow_wcoss venv is loaded, not system Python."
    )


def test_uwtools_version():
    """uwtools must be pinned to 2.16.0 in the active venv."""
    version = importlib.metadata.version("uwtools")
    assert version == "2.16.0", (
        f"Expected uwtools 2.16.0 but found {version}. "
        "Check that the correct venv is active."
    )


def test_uwtools_schema_loading():
    """Core uwtools API must load and return a valid schema dict."""
    import uwtools.api.ww3 as ww3

    schema_dict = ww3.schema()
    assert isinstance(schema_dict, dict), (
        "ww3.schema() did not return a dict — uwtools API may be broken."
    )


def test_ecflow_import():
    """
    Check whether ecflow can be imported from within the uwtools venv.

    The ecflow module on WCOSS2 is built against Python 3.8.6, but the
    uwtools venv uses Python 3.12. This test is expected to fail due to
    the Python version mismatch. Determine whether ecflow is required by
    uw-aigfs before treating failure here as a blocker.
    """
    try:
        import ecflow

        version = getattr(ecflow, "__version__", "unknown")
        # If we get here, it worked — report the version
        print(f"\necflow imported successfully. Version: {version}")
    except ImportError as e:
        pytest.fail(
            f"ecflow import failed: {e}\n"
            "Likely cause: ecflow on WCOSS2 is built against Python 3.8.6 "
            "but the uwtools venv uses Python 3.12. "
            "Determine whether ecflow is required by uw-aigfs before treating "
            "this as a blocker."
        )
