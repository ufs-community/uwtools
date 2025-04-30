from pathlib import Path
from textwrap import dedent

import yaml
from pytest import fixture
from testbook import testbook

base = Path("fixtures/config")


@fixture(scope="module")
def tb():
    with testbook("config.ipynb", execute=True) as tb:
        yield tb


def test_config_get_config(load, tb):
    config1_str = load(base / "get-config.yaml")
    assert tb.ref("config1") == yaml.safe_load(config1_str)
    assert tb.cell_output_text(5) == config1_str
    assert config1_str in tb.cell_output_text(7)
    assert tb.cell_output_text(9) == "message:\n  greeting: Hi\n  recipient: Earth"


def test_config_depth(tb):
    assert tb.cell_output_text(11) == "greeting=Salutations\nrecipient=Mars"
    assert tb.cell_output_text(13) == "Cannot instantiate depth-1 SHConfig with depth-2 config"
    assert tb.cell_output_text(15) == "[message]\ngreeting = Salutations\nrecipient = Mars"
    assert tb.cell_output_text(17) == "Cannot instantiate depth-2 INIConfig with depth-1 config"


def test_config_realize(load, tb):
    # Get config file data to compare to cell output.
    config_str = load(base / "get-config.yaml")
    config_dict = yaml.safe_load(config_str)
    update_config_str = load(base / "base-config.nml")
    # Ensure that cell output text matches expectations.
    assert tb.cell_output_text(21) == str(config_dict)
    assert tb.cell_output_text(23) == config_str
    assert tb.cell_output_text(25) == str(config_dict)
    for item in config_dict.items():
        assert item[0] + "=" + item[1] in tb.cell_output_text(27)
    assert tb.cell_output_text(29) == update_config_str
    updated_dict = (
        "'sender_id': '{{ id }}'",
        "'message': 'Salutations, Mars!'",
        "'sent': True",
    )
    assert all(x in tb.cell_output_text(31) for x in updated_dict)
    assert tb.cell_output_text(33) == load("tmp/updated-config.nml")
    assert tb.cell_output_text(35) == load(base / "keys-config.yaml")
    assert tb.cell_output_text(37) == "message: Good morning, Venus!"
    assert tb.cell_output_text(39) == update_config_str
    expected_log = (
        "memo.sender_id: {{ id }}",
        "memo.message: {{ greeting }}, {{ recipient }}!",
    )
    assert all(x in tb.cell_output_text(41) for x in expected_log)
    assert tb.cell_output_text(43) == update_config_str
    assert tb.cell_output_text(45) == "Config could not be totally realized"
    total_dict = ("'sender_id': '321'", "'message': 'Salutations, Mars!'", "'sent': True")
    assert all(x in tb.cell_output_text(47) for x in total_dict)
    assert tb.cell_output_text(49) == load("tmp/config-total.nml")


def test_config_realize_to_dict(load, tb):
    assert tb.cell_output_text(51) == load(base / "get-config.yaml")
    config_out = ("'id': '456'", "'greeting': 'Hello'", "'recipient': 'World'")
    assert all(x in tb.cell_output_text(53) for x in config_out)


def test_config_compare(load, tb):
    base_cfg = load(base / "base-config.nml")
    assert base_cfg in tb.cell_output_text(57)
    assert load(base / "alt-config.nml") in tb.cell_output_text(57)
    diff_cmp = """
    INFO - fixtures/config/base-config.nml
    INFO + fixtures/config/alt-config.nml
    INFO ---------------------------------------------------------------------
    INFO ↓ ? = info | -/+ = line unique to - or + file | blank = matching line
    INFO ---------------------------------------------------------------------
    INFO   memo:
    INFO     message: '{{ greeting }}, {{ recipient }}!'
    INFO     sender_id: '{{ id }}'
    INFO -   sent: false
    INFO +   sent: true
    """
    assert all(x in tb.cell_output_text(59) for x in dedent(diff_cmp).strip().split("\n"))
    assert base_cfg == load("tmp/config-copy.nml")  # cell 61 creates this copy
    same_cmp = ("INFO - fixtures/config/base-config.nml", "INFO + tmp/config-copy.nml", "True")
    assert all(x in tb.cell_output_text(63) for x in same_cmp)
    assert "ERROR Formats do not match: yaml vs nml" in tb.cell_output_text(65)


def test_config_validate(load, tb):
    assert tb.cell_output_text(69) == load(base / "get-config.yaml")
    assert tb.cell_output_text(71) == load(base / "validate.jsonschema")
    valid_out = ("INFO 0 schema-validation errors found", "True")
    assert all(x in tb.cell_output_text(73) for x in valid_out)
    invalid_out = (
        "ERROR 1 schema-validation error found",
        "ERROR   47 is not of type 'string'",
        "False",
    )
    assert all(x in tb.cell_output_text(75) for x in invalid_out)


def test_config_cfg_classes(load, tb):
    assert tb.cell_output_text(79) == load(base / "fruit-config.ini")
    assert tb.cell_output_text(81) == "True"
    diff_cmp = """
    INFO ---------------------------------------------------------------------
    INFO ↓ ? = info | -/+ = line unique to - or + file | blank = matching line
    INFO ---------------------------------------------------------------------
    INFO   fruit count:
    INFO     apples: '3'
    INFO -   grapes: '{{ grape_count }}'
    INFO +   grapes: '8'
    INFO -   kiwis: '2'
    INFO ?           ^
    INFO +   kiwis: '1'
    INFO ?           ^
    """
    assert all(x in tb.cell_output_text(83) for x in dedent(diff_cmp).strip().split("\n"))
    assert "grapes = 15" in tb.cell_output_text(85)
    assert tb.cell_output_text(89) == load("tmp/fruits.ini")
    dump_dict = ("[fruit count]", "oranges = 4", "blueberries = 9")
    assert all(x in tb.cell_output_text(91) for x in dump_dict)
    updated_vals = ("kiwis = 4", "raspberries = 12")
    assert all(x in tb.cell_output_text(93) for x in updated_vals)
