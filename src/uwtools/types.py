from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from uwtools.config.formats.base import Config

SupplementalConfigs = Optional[List[Union[dict, Config, DefinitePath]]]
DefinitePath = Union[Path, str]
OptionalPath = Optional[DefinitePath]


@dataclass
class ExistAct:
    """
    Possible actions to take when a directory already exists.
    """

    delete: str = "delete"
    quit: str = "quit"
    rename: str = "rename"
