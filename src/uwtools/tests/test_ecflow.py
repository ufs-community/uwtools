"""
Tests for uwtools.ecflow module.
"""

from pytest import mark

from uwtools.ecflow import _ECFlowDef


class TestECFlowDef:
    @mark.parametrize(
        ("key", "expected"),
        [
            ("task_foo", ("task", "foo")),
            ("family_my_family", ("family", "my_family")),
            ("suite_prod", ("suite", "prod")),
            ("vars", ("vars", "")),
        ],
    )
    def test__tag_name(self, key, expected):
        # _tag_name is called on self, so we need a minimal instance.
        ecf = _ECFlowDef(config={"ecflow": {}})
        assert ecf._tag_name(key) == expected
