"""
Custom exceptions for the UWTools package.
"""


class UWError(Exception):
    """
    An abstract class representing generic exceptions for UWTools.
    """


class UWConfigError(UWError):
    """
    UWTools exception for Config Object error handling.
    """
