from pathlib import Path
from unittest.mock import patch

from pytest import mark

from uwtools.api import rocoto


def test_api_rocoto_realize():
    path1, path2 = Path("foo"), Path("bar")
    with patch.object(rocoto, "_realize") as _realize:
        rocoto.realize(config=path1, output_file=path2)
    _realize.assert_called_once_with(config=path1, output_file=path2)


@mark.parametrize("f", [Path, str])
def test_api_rocoto_run(f, utc):
    cycle = utc()
    database = f("/path/to/rocoto.db")
    task = "foo"
    workflow = f("/path/to/rocoto.xml")
    with patch.object(rocoto, "_run") as _run:
        rocoto.run(cycle=cycle, database=database, task=task, workflow=workflow)
    _run.assert_called_once_with(
        cycle=cycle, database=Path(database), task=task, workflow=Path(workflow)
    )


def test_api_rocoto_validate():
    path = Path("foo")
    with patch.object(rocoto, "_validate") as _validate:
        rocoto.validate(xml_file=path)
    _validate.assert_called_once_with(xml_file=path)
