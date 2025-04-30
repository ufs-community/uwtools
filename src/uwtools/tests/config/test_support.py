"""
Tests for uwtools.config.jinja2 module.
"""

from collections import OrderedDict

import yaml
from pytest import fixture, mark, raises

from uwtools.config import support
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError

# Fixtures


@fixture
def loader():
    yaml.add_representer(support.UWYAMLConvert, support.UWYAMLTag.represent)
    return yaml.SafeLoader("")


# Tests


@mark.parametrize(
    ("d", "n"), [({1: 42}, 1), ({1: {2: 42}}, 2), ({1: {2: {3: 42}}}, 3), ({1: {}}, 2)]
)
def test_config_support_depth(d, n):
    assert support.depth(d) == n


def test_config_support_dict_to_yaml_str(capsys):
    xs = " ".join("x" * 999)
    expected = f"xs: {xs}"
    cfgobj = YAMLConfig({"xs": xs})
    assert repr(cfgobj) == expected
    assert str(cfgobj) == expected
    cfgobj.dump()
    assert capsys.readouterr().out.strip() == expected


def test_config_support_from_od():
    assert support.from_od(d=OrderedDict([("example", OrderedDict([("key", "value")]))])) == {
        "example": {"key": "value"}
    }


def test_config_support_log_and_error(logged):
    msg = "Something bad happened"
    with raises(UWConfigError) as e:
        raise support.log_and_error(msg)
    assert msg in str(e.value)
    assert logged(msg)


class TestUWYAMLConvert:
    """
    Tests for class uwtools.config.support.UWYAMLConvert.
    """

    def comp(self, ts: support.UWYAMLConvert, s: str):
        assert yaml.dump(ts, default_flow_style=True).strip() == s

    @mark.parametrize(
        ("tag", "val", "val_type"),
        [
            ("!bool", True, "bool"),
            ("!dict", {1: 2}, "dict"),
            ("!float", 3.14, "float"),
            ("!int", 42, "int"),
            ("!list", [1, 2], "list"),
        ],
    )
    def test_UWYAMLConvert_bad_non_str(self, loader, tag, val, val_type):
        with raises(UWConfigError) as e:
            support.UWYAMLConvert(loader, yaml.ScalarNode(tag=tag, value=val))
        msg = "Value tagged %s must be type 'str' (not '%s') in: %s %s"
        assert str(e.value) == msg % (tag, val_type, tag, val)

    # These tests bypass YAML parsing, constructing nodes with explicit string values. They then
    # demonstrate that those nodes' convert() methods return representations in the type specified
    # by the tag.

    @mark.parametrize(("value", "expected"), [("False", False), ("True", True)])
    def test_UWYAMLConvert_bool_values(self, expected, loader, value):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!bool", value=value))
        assert ts.converted == expected

    def test_UWYAMLConvert_datetime_no(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!datetime", value="foo"))
        with raises(ValueError, match="Invalid isoformat string"):
            assert ts.converted

    def test_UWYAMLConvert_datetime_ok(self, loader, utc):
        ts = support.UWYAMLConvert(
            loader, yaml.ScalarNode(tag="!datetime", value="2024-08-09 12:22:42")
        )
        assert ts.converted == utc(2024, 8, 9, 12, 22, 42)
        self.comp(ts, "!datetime '2024-08-09 12:22:42'")

    def test_UWYAMLConvert_dict_no(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!dict", value="42"))
        with raises(TypeError):
            assert ts.converted

    def test_UWYAMLConvert_dict_ok(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!dict", value="{a0: 0,a1: 1,}"))
        assert ts.converted == {"a0": 0, "a1": 1}
        self.comp(ts, "!dict '{a0: 0,a1: 1,}'")

    def test_UWYAMLConvert_float_no(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!float", value="foo"))
        with raises(ValueError, match="could not convert string to float"):
            assert ts.converted

    def test_UWYAMLConvert_float_ok(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!float", value="3.14"))
        assert ts.converted == 3.14
        self.comp(ts, "!float '3.14'")

    def test_UWYAMLConvert_int_no(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!int", value="foo"))
        with raises(ValueError, match="invalid literal"):
            assert ts.converted

    def test_UWYAMLConvert_int_ok(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!int", value="42"))
        assert ts.converted == 42
        self.comp(ts, "!int '42'")

    def test_UWYAMLConvert_list_no(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!list", value="null"))
        with raises(TypeError):
            assert ts.converted

    def test_UWYAMLConvert_list_ok(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!list", value="[1,2,3,]"))
        assert ts.converted == [1, 2, 3]
        self.comp(ts, "!list '[1,2,3,]'")

    def test_UWYAMLConvert___repr__(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!list", value="[ 1,2,3, ]"))
        assert repr(ts) == "!list [1, 2, 3]"

    def test_UWYAMLConvert___str__(self, loader):
        ts = support.UWYAMLConvert(loader, yaml.ScalarNode(tag="!list", value="[ 1,2,3, ]"))
        assert str(ts) == "[1, 2, 3]"


class TestUWYAMLGlob:
    """
    Tests for class uwtools.config.support.UWYAMLGlob.
    """

    def test_UWYAMLGlob(self, loader):
        yaml.add_representer(support.UWYAMLGlob, support.UWYAMLTag.represent)
        node = support.UWYAMLGlob(loader, yaml.ScalarNode(tag="!glob", value="/path/to/*"))
        assert repr(node) == "!glob /path/to/*"
        assert str(node) == "!glob /path/to/*"


class TestUWYAMLRemove:
    """
    Tests for class uwtools.config.support.UWYAMLRemove.
    """

    def test_UWYAMLRemove(self, loader):
        yaml.add_representer(support.UWYAMLRemove, support.UWYAMLTag.represent)
        node = support.UWYAMLRemove(loader, yaml.ScalarNode(tag="!remove", value=""))
        assert repr(node) == "!remove"
        assert str(node) == "!remove"

    def test_UWYAMLRemove_dump(self, tmp_path):
        expected = "ns: !remove [1, 2, 3]"
        old = tmp_path / "old.yaml"
        old.write_text(expected)
        c = YAMLConfig(old)
        new = tmp_path / "new.yaml"
        c.dump(new)
        assert new.read_text().strip() == expected
