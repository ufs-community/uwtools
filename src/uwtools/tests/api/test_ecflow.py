from pathlib import Path
from unittest.mock import patch

from uwtools.api import ecflow


def test_api_ecflow_realize():
    path1, path2 = Path("foo"), Path("bar")
    with patch.object(ecflow, "_realize") as _realize:
        ecflow.realize(config=path1, output_path=path2)
    _realize.assert_called_once_with(config=path1, output_path=path2, scripts_path=None)


def test_api_ecflow_realize__with_scripts():
    path1, path2, path3 = Path("foo"), Path("bar"), Path("baz")
    with patch.object(ecflow, "_realize") as _realize:
        ecflow.realize(config=path1, output_path=path2, scripts_path=path3)
    _realize.assert_called_once_with(config=path1, output_path=path2, scripts_path=path3)


def test_api_ecflow_validate():
    path = Path("foo")
    with patch.object(ecflow, "_validate") as _validate:
        ecflow.validate(yaml_file=path)
    _validate.assert_called_once_with(yaml_file=path)
