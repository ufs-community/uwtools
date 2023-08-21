"""
Custom exceptions for the UWTools package.
"""

from abc import ABC


class UWError(ABC, Exception):
    """
    An abstract class representing all exceptions for UWTools.
    """


class UWConfigError(UWError):
    """
    UWTools exception for Config Object error handling.
    """
