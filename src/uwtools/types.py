from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

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
