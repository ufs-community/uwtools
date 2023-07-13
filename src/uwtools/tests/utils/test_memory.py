# pylint: disable=missing-function-docstring
"""
Tests for uwtools.utils.file_helpers module.
"""

from uwtools.utils import Memory


def test_memory_conversions():
    assert str(Memory("100MB").convert("KB")) == "100000KB"
    assert str(Memory("100KB").convert("MB")) == "0.1MB"
    assert str(Memory("100GB").convert("KB")) == "100000000KB"
    assert str(Memory("100MB").convert("GB")) == "0.1GB"
    assert str(Memory("100GB").convert("MB")) == "100000MB"
    assert str(Memory("100KB").convert("GB")) == "9.999999999999999e-05GB"
