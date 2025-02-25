# pylint: disable=redefined-outer-name

from __future__ import annotations

from pathlib import Path
from typing import Callable

from pytest import fixture


@fixture
def load() -> Callable:
    def load(path: str | Path) -> str:
        return Path(path).read_text(encoding="utf-8").strip()

    return load
