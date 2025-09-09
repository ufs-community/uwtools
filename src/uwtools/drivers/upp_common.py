"""
Common UPP logic.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from iotaa import asset

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.upp_assets import UPPAssets
from uwtools.exceptions import UWConfigError
from uwtools.fs import Copier, Linker
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink

if TYPE_CHECKING:
    from uwtools.drivers.upp import UPP
    from uwtools.drivers.upp_assets import UPPAssets

GENPROCTYPE_IDX = 8
NFIELDS = 16
NPARAMS = 42


# Workflow support functions:


def control_file(obj: UPP | UPPAssets):
    yield obj.taskname("GRIB control file")
    yield filecopy(src=Path(obj.config["control_file"]), dst=obj.rundir / "postxconfig-NT.txt")


def files_copied(obj: UPP | UPPAssets):
    yield obj.taskname("files copied")
    yield [
            Copier(
                config=self.config.get("files_to_copy", {}),
                target_dir=self.rundir
                ).go()
    ]


def files_linked(obj: UPP | UPPAssets):
    yield obj.taskname("files linked")
    yield [
            Linker(
                config=self.config.get("files_to_link", {}),
                target_dir=self.rundir
                ).go()
    ]


def namelist_file(obj: UPP | UPPAssets):
    path = namelist_path(obj)
    yield obj.taskname(str(path))
    yield asset(path, path.is_file)
    base_file = obj.config[STR.namelist].get(STR.basefile)
    yield file(Path(base_file)) if base_file else None
    obj.create_user_updated_config(
        config_class=NMLConfig,
        config_values=obj.config[STR.namelist],
        path=path,
        schema=obj.namelist_schema(),
    )


# Helpers:


def namelist_path(obj: UPP | UPPAssets) -> Path:
    """
    The path to the namelist file.
    """
    return obj.rundir / "itag"


def output(obj: UPP | UPPAssets) -> dict[str, Path] | dict[str, list[Path]]:
    """
    Returns a description of the file(s) created when this component runs.
    """
    # Read the control file into an array of lines. Get the number of blocks (one per output
    # GRIB file) and the number of variables per block. For each block, construct a filename
    # from the block's identifier and the suffix defined above.
    cf = obj.config["control_file"]
    try:
        lines = Path(cf).read_text().split("\n")
    except (FileNotFoundError, PermissionError) as e:
        msg = f"Could not open UPP control file {cf}"
        raise UWConfigError(msg) from e
    suffix = ".GrbF%02d" % int(obj.leadtime.total_seconds() / 3600)
    nblocks, lines = int(lines[0]), lines[1:]
    nvars, lines = list(map(int, lines[:nblocks])), lines[nblocks:]
    paths = []
    for _ in range(nblocks):
        identifier = lines[0]
        paths.append(obj.rundir / (identifier + suffix))
        fields, lines = lines[:NFIELDS], lines[NFIELDS:]
        _, lines = (lines[0], lines[1:]) if fields[GENPROCTYPE_IDX] == "ens_fcst" else (None, lines)
        lines = lines[NPARAMS * nvars.pop() :]
    return {"paths": paths}
