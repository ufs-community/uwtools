# pylint: disable=missing-function-docstring
"""
Tests for uwtools.config.jinja2 module.
"""

import pytest

from uwtools.config import support


@pytest.mark.parametrize("d,n", [({1: 88}, 1), ({1: {2: 88}}, 2), ({1: {2: {3: 88}}}, 3)])
def test_depth(d, n):
    assert support.depth(d) == n
