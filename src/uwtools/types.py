from dataclasses import dataclass


@dataclass
class ExistAct:
    """
    Possible actions to take when a directory already exists.
    """

    delete: str = "delete"
    quit: str = "quit"
    rename: str = "rename"
