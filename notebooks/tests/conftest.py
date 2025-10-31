from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pytest import fixture

if TYPE_CHECKING:
    from collections.abc import Callable


@fixture
def load() -> Callable:
    def load(path: str | Path) -> str:
        return Path(path).read_text(encoding="utf-8").strip()

    return load
