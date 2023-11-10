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

# Helper functions
