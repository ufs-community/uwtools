"""
Custom uwtools exceptions.
"""


class UWError(Exception):
    """
    A class representing generic uwtools exceptions.
    """


class UWConfigError(UWError):
    """
    Exception for generic config error handling.
    """


class UWConfigRealizeError(UWConfigError):
    """
    Exception for issues arising from config realization.
    """


class UWNotImplementedError(UWError):
    """
    Exception for signaling that uwtools has not (yet) implemented something.
    """


class UWTemplateRenderError(UWError):
    """
    Exception for issues arising from template rendering.
    """
