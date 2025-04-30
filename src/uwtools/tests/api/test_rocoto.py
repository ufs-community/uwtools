from pathlib import Path
from unittest.mock import patch

from uwtools.api import rocoto


def test_realize():
    path1, path2 = Path("foo"), Path("bar")
    with patch.object(rocoto, "_realize") as _realize:
        rocoto.realize(config=path1, output_file=path2)
    _realize.assert_called_once_with(config=path1, output_file=path2)


def test_validate():
    path = Path("foo")
    with patch.object(rocoto, "_validate") as _validate:
        rocoto.validate(xml_file=path)
    _validate.assert_called_once_with(xml_file=path)
