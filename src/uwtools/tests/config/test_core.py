# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.config.core module.
"""
# Tests


# def test_Config___repr__(capsys, nml_cfgobj):
#     print(nml_cfgobj)
#     assert yaml.safe_load(capsys.readouterr().out)["nl"]["n"] == 88


# def test_Config_characterize_values(nml_cfgobj):
#     d = {1: "", 2: None, 3: "{{ n }}", 4: {"a": 88}, 5: [{"b": 99}], 6: "string"}
#     complete, empty, template = nml_cfgobj.characterize_values(values=d, parent="p")
#     assert complete == ["    p4", "    p4.a", "    pb", "    p5", "    p6"]
#     assert empty == ["    p1", "    p2"]
#     assert template == ["    p3: {{ n }}"]


# def test_Config_reify_scalar_str(nml_cfgobj):
#     for x in ["true", "yes", "TRUE"]:
#         assert nml_cfgobj.reify_scalar_str(x) is True
#     for x in ["false", "no", "FALSE"]:
#         assert nml_cfgobj.reify_scalar_str(x) is False
#     assert nml_cfgobj.reify_scalar_str("88") == 88
#     assert nml_cfgobj.reify_scalar_str("'88'") == "88"  # quoted int not converted
#     assert nml_cfgobj.reify_scalar_str("3.14") == 3.14
#     assert nml_cfgobj.reify_scalar_str("NA") == "NA"  # no conversion
#     assert nml_cfgobj.reify_scalar_str("@[foo]") == "@[foo]"  # no conversion for YAML exceptions
#     with raises(AttributeError) as e:
#         nml_cfgobj.reify_scalar_str([1, 2, 3])
#     assert "'list' object has no attribute 'read'" in str(e.value)  # Exception on unintended list


# Helper functions


# @fixture
# def nml_cfgobj(tmp_path):
#     # Use NMLConfig to exercise methods in Config abstract base class.
#     path = tmp_path / "cfg.nml"
#     with open(path, "w", encoding="utf-8") as f:
#         f.write("&nl n = 88 /")
#     return NMLConfig(config_file=path)
