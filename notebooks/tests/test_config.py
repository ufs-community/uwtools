import yaml
from testbook import testbook


def test_get_config():
    with open("fixtures/config/get-config.yaml", "r", encoding="utf-8") as f:
        config1_str = f.read().rstrip()
        config1_dict = yaml.safe_load(config1_str)
    with testbook("config.ipynb", execute=True) as tb:
        assert tb.ref("config1") == config1_dict
        assert tb.cell_output_text(5) == config1_str
        assert config1_str in tb.cell_output_text(7)
        assert tb.cell_output_text(9) == "message:\n  greeting: Hi\n  recipient: Earth"


def test_depth():
    with testbook("config.ipynb", execute=True) as tb:
        assert tb.cell_output_text(11) == "greeting=Salutations\nrecipient=Mars"
        assert tb.cell_output_text(13) == "Cannot instantiate depth-1 SHConfig with depth-2 config"
        assert tb.cell_output_text(15) == "[message]\ngreeting = Salutations\nrecipient = Mars"
        assert tb.cell_output_text(17) == "Cannot instantiate depth-2 INIConfig with depth-1 config"


def test_realize():
    # Get config file data to compare to cell output.
    with open("fixtures/config/get-config.yaml", "r", encoding="utf-8") as f:
        config_str = f.read().rstrip()
        config_dict = yaml.safe_load(config_str)
    with open("fixtures/config/base-config.nml", "r", encoding="utf-8") as f:
        update_config_str = f.read().rstrip()
    with open("fixtures/config/keys-config.yaml", "r", encoding="utf-8") as f:
        keys_config_str = f.read().rstrip()
    with testbook("config.ipynb", execute=True) as tb:
        with open("tmp/updated-config.nml", "r", encoding="utf-8") as f:
            updated_config = f.read().rstrip()
        with open("tmp/config-total.nml", "r", encoding="utf-8") as f:
            total_config = f.read().rstrip()
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
        assert tb.cell_output_text(33) == updated_config
        assert tb.cell_output_text(35) == keys_config_str
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
        assert tb.cell_output_text(49) == total_config


def test_realize_to_dict():
    with open("fixtures/config/get-config.yaml", "r", encoding="utf-8") as f:
        config_str = f.read().rstrip()
    with testbook("config.ipynb", execute=True) as tb:
        assert tb.cell_output_text(51) == config_str
        config_out = ("'id': '456'", "'greeting': 'Hello'", "'recipient': 'World'")
        assert all(x in tb.cell_output_text(53) for x in config_out)


def test_compare():
    with open("fixtures/config/base-config.nml", "r", encoding="utf-8") as f:
        base_cfg = f.read().rstrip()
    with open("fixtures/config/alt-config.nml", "r", encoding="utf-8") as f:
        alt_cfg = f.read().rstrip()
    with open("tmp/config-copy.nml", "r", encoding="utf-8") as f:
        cp_cfg = f.read().rstrip()
    with testbook("config.ipynb", execute=True) as tb:
        assert base_cfg in tb.cell_output_text(57)
        assert alt_cfg in tb.cell_output_text(57)
        diff_cmp = (
            "INFO - fixtures/config/base-config.nml",
            "INFO + fixtures/config/alt-config.nml",
            "INFO memo:            sent:  - False + True",
            "False",
        )
        assert all(x in tb.cell_output_text(59) for x in diff_cmp)
        assert base_cfg == cp_cfg  # cell 61 creates this copy
        same_cmp = ("INFO - fixtures/config/base-config.nml", "INFO + tmp/config-copy.nml", "True")
        assert all(x in tb.cell_output_text(63) for x in same_cmp)


def test_validate():
    with open("fixtures/config/validate.jsonschema", "r", encoding="utf-8") as f:
        schema = f.read().rstrip()
    with testbook("config.ipynb", execute=True) as tb:
        assert tb.cell_output_text(67) == schema
        valid_out = ("INFO 0 UW schema-validation errors found", "True")
        assert all(x in tb.cell_output_text(69) for x in valid_out)
        invalid_out = (
            "ERROR 1 UW schema-validation error found",
            "ERROR   47 is not of type 'string'",
            "False",
        )
        assert all(x in tb.cell_output_text(71) for x in invalid_out)


def test_cfg_classes():
    with open("fixtures/config/fruit-config.ini", "r", encoding="utf-8") as f:
        cfg = f.read().rstrip()
    with testbook("config.ipynb", execute=True) as tb:
        with open("tmp/fruits.ini", "r", encoding="utf-8") as f:
            dump = f.read().rstrip()
        assert tb.cell_output_text(75) == cfg
        assert tb.cell_output_text(77) == "True"
        diff_cmp = (
            "INFO fruit count:          grapes:  - {{ grape_count }} + 8",
            "INFO fruit count:           kiwis:  - 2 + 1",
            "False",
        )
        assert all(x in tb.cell_output_text(79) for x in diff_cmp)
        assert "grapes = 15" in tb.cell_output_text(81)
        assert tb.cell_output_text(85) == dump
        dump_dict = ("[fruit count]", "oranges = 4", "blueberries = 9")
        assert all(x in tb.cell_output_text(87) for x in dump_dict)
        updated_vals = ("kiwis = 4", "raspberries = 12")
        assert all(x in tb.cell_output_text(89) for x in updated_vals)
