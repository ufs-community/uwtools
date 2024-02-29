"""
Custom exceptions for the UWTools package.
"""


class UWError(Exception):
    """
    A class representing generic exceptions for UWTools.
    """


class UWConfigError(UWError):
    """
    UWTools exception for general Config object error handling.
    """


class UWConfigRealizeError(UWConfigError):
    """
    UWTools exception arising from issues realizing configs.
    """
