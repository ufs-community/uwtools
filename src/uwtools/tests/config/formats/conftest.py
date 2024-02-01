# pylint: disable=duplicate-code,missing-function-docstring
"""
Pytest fixtures for package uwtools.config.formats tests.
"""

# NB: pytest implicitly imports files named conftest.py into test modules in the current directory
# and in subdirectories.

from pytest import fixture


@fixture
def salad_base():
    return {
        "salad": {
            "base": "kale",
            "fruit": "banana",
            "vegetable": "tomato",
            "how_many": 12,
            "dressing": "balsamic",
        }
    }
