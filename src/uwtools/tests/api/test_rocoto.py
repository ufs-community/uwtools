from pathlib import Path
from unittest.mock import patch

from pytest import mark, raises

from uwtools.api import rocoto
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWError


@mark.parametrize("f", [Path, str])
@mark.parametrize("task", ["foo", None])
def test_api_rocoto_iterate(f, task, utc):
    cycle = utc()
    database = f("/path/to/rocoto.db")
    rate = 11
    workflow = f("/path/to/rocoto.xml")
    with patch.object(rocoto, "_iterate") as _iterate:
        rocoto.iterate(cycle=cycle, database=database, rate=rate, task=task, workflow=workflow)
    _iterate.assert_called_once_with(
        cycle=cycle, database=Path(database), rate=rate, task=task, workflow=Path(workflow)
    )


def test_api_rocoto_realize():
    path1, path2 = Path("foo"), Path("bar")
    with patch.object(rocoto, "_realize") as _realize:
        rocoto.realize(config=path1, output_file=path2)
    _realize.assert_called_once_with(config=path1, output_file=path2, key_path=None)


@mark.parametrize(
    ("config", "expected"),
    [
        ({"rocoto": {}}, {"rocoto": {}}),
        (Path("foo"), Path("foo")),
        ("foo", Path("foo")),
        (YAMLConfig({"rocoto": {}}), YAMLConfig({"rocoto": {}})),
    ],
)
@mark.parametrize("key_path", [None, ["a", "b"]])
def test_api_rocoto_validate(config, expected, key_path):
    with patch.object(rocoto, "_validate") as _validate:
        assert rocoto.validate(config=config, key_path=key_path) is True
    _validate.assert_called_once_with(config=expected, key_path=key_path)


def test_api_rocoto_validate__no_stdin_no_config():
    with raises(UWError) as e:
        rocoto.validate()
    assert "Set stdin_ok=True to permit read from stdin" in str(e.value)


def test_api_rocoto_validate__stdin():
    with patch.object(rocoto, "_validate") as _validate:
        assert rocoto.validate(stdin_ok=True) is True
    _validate.assert_called_once_with(config=None, key_path=None)


def test_api_rocoto_validate_xml():
    path = Path("foo")
    with patch.object(rocoto, "_validate_xml_file") as _validate_xml_file:
        rocoto.validate_xml(xml_file=path)
    _validate_xml_file.assert_called_once_with(xml_file=path)
