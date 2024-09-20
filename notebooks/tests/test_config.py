import yaml
from pytest import raises
from testbook import testbook
from testbook.exceptions import TestbookRuntimeError
from uwtools.exceptions import UWConfigError, UWConfigRealizeError

all_cells = [*range(0, 57)]
err_cells = [13, 17, 45]
non_err_cells = list(filter(lambda n: n not in err_cells, all_cells))


def test_get_config():
    with open("fixtures/config/get-config.yaml", "r", encoding="utf-8") as f:
        config1_str = f.read().rstrip()
        config1_dict = yaml.safe_load(config1_str)
    with testbook("config.ipynb", execute=non_err_cells) as tb:
        assert tb.ref("config1") == config1_dict
        assert tb.cell_output_text(5) == config1_str
        assert tb.cell_output_text(7) == config1_str
        assert tb.cell_output_text(9) == "message:\n  greeting: Hi\n  recipient: Earth"


def test_depth():
    with testbook("config.ipynb", execute=non_err_cells) as tb:
        assert tb.cell_output_text(11) == "greeting=Salutations\nrecipient=Mars"
        assert tb.cell_output_text(15) == "[message]\ngreeting = Salutations\nrecipient = Mars"


def test_depth_errs():
    with raises(TestbookRuntimeError) as e:
        with testbook("config.ipynb", execute=[1, 13]):
            pass
    assert e.value.eclass == UWConfigError
    assert e.value.evalue == "Cannot instantiate depth-1 SHConfig with depth-2 config"
    with raises(TestbookRuntimeError) as e:
        with testbook("config.ipynb", execute=[1, 17]):
            pass
    assert e.value.eclass == UWConfigError
    assert e.value.evalue == "Cannot instantiate depth-2 INIConfig with depth-1 config"


def test_realize():
    # Get config file data to compare to cell output.
    with open("fixtures/config/get-config.yaml", "r", encoding="utf-8") as f:
        config_str = f.read().rstrip()
        config_dict = yaml.safe_load(config_str)
    with open("fixtures/config/base-config.nml", "r", encoding="utf-8") as f:
        update_config_str = f.read().rstrip()
    with open("fixtures/config/keys-config.yaml", "r", encoding="utf-8") as f:
        keys_config_str = f.read().rstrip()
    with testbook("config.ipynb", execute=non_err_cells) as tb:
        # Ensure that cell output text matches expectations.
        assert tb.cell_output_text(21) == str(config_dict)
        assert tb.cell_output_text(23) == config_str
        assert tb.cell_output_text(25) == str(config_dict)
        for item in config_dict.items():
            assert item[0] + "=" + item[1] in tb.cell_output_text(27)
        assert tb.cell_output_text(29) == update_config_str
        assert (
            "'sender_id': '{{ id }}'" in tb.cell_output_text(31)
            and "'message': 'Salutations, Mars!'" in tb.cell_output_text(31)
            and "'sent': True" in tb.cell_output_text(31)
        )
        assert (
            "sender_id = '{{ id }}'" in tb.cell_output_text(33)
            and "message = 'Salutations, Mars!'" in tb.cell_output_text(33)
            and "sent = .true." in tb.cell_output_text(33)
        )
        assert tb.cell_output_text(35) == keys_config_str
        assert "message: Good morning, Venus!" in tb.cell_output_text(37)
        assert tb.cell_output_text(39) == update_config_str
        assert "memo.sender_id: {{ id }}" in tb.cell_output_text(
            41
        ) and "memo.message: {{ greeting }}, {{ recipient }}!" in tb.cell_output_text(41)
        assert tb.cell_output_text(43) == update_config_str
        assert (
            "'sender_id': '321'" in tb.cell_output_text(47)
            and "'message': 'Salutations, Mars!'" in tb.cell_output_text(47)
            and "'sent': True" in tb.cell_output_text(47)
        )
        assert (
            "sender_id = '321'" in tb.cell_output_text(49)
            and "message = 'Salutations, Mars!'" in tb.cell_output_text(49)
            and "sent = .true." in tb.cell_output_text(49)
        )


def test_realize_errs():
    with raises(TestbookRuntimeError) as e:
        with testbook("config.ipynb", execute=[1, 45]):
            pass
    assert e.value.eclass == UWConfigRealizeError
    assert e.value.evalue == "Config could not be totally realized"


def test_realize_to_dict():
    with open("fixtures/config/get-config.yaml", "r", encoding="utf-8") as f:
        config_str = f.read().rstrip()
    with testbook("config.ipynb", execute=non_err_cells) as tb:
        assert tb.cell_output_text(53) == config_str
        assert (
            "'id': '456'" in tb.cell_output_text(55)
            and "'greeting': 'Hello'" in tb.cell_output_text(55)
            and "'recipient': 'World'" in tb.cell_output_text(55)
        )
