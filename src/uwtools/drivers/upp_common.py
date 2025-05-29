"""
A UPP common mixin class.
"""

from pathlib import Path


class UPPCommon:
    """
    A UPP common mixin class.
    """

    # Facts specific to the supported UPP version:

    GENPROCTYPE_IDX = 8
    NFIELDS = 16
    NPARAMS = 42

    # Helper methods:

    @property
    def namelist_path(self) -> Path:
        """
        The path to the namelist file.
        """
        return self.rundir / "itag"

    # Placeholders to be overridden by mixing-in classes:

    @property
    def rundir(self) -> Path:
        return Path("/dev/null")
