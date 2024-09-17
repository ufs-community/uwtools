import os

import yaml
from testbook import testbook
from uwtools.exceptions import UWConfigError, UWConfigRealizeError

all_cells = [*range(0,57)]
err_cells = [13,17,45]
non_err_cells = list(filter(lambda n: n not in err_cells, all_cells))

def test_get_config():
    config2_str = 'message:\n  greeting: Hi\n  recipient: Earth'
    # Get the config file as text and dict.
    with open("fixtures/config/getConfig.yaml", "r", encoding="utf-8") as f:
        config1_str = f.read().rstrip()
        config1_dict = yaml.safe_load(config1_str)
    with testbook("config.ipynb", execute=non_err_cells) as tb:
        #  Ensure that notebook variables have the correct values
        assert tb.ref("config1") == config1_dict
        assert tb.ref("config2") == yaml.safe_load(config2_str)
        # Ensure that cell output text matches expectations.
        assert tb.cell_output_text(5) == config1_str
        assert tb.cell_output_text(7) == config1_str
        assert tb.cell_output_text(9) == config2_str

def test_depth():
    with testbook("config.ipynb", execute=non_err_cells) as tb:
        assert 'greeting=Salutations\nrecipient=Mars' == tb.cell_output_text(11)
        assert '[message]\ngreeting = Salutations\nrecipient = Mars' == tb.cell_output_text(15)

def test_depth_errs():
    try:
        with testbook("config.ipynb", execute=[1,13]):
            pass
    except:
        assert True
    else:
        assert False

    try:
        with testbook("config.ipynb", execute=[1,17]):
            pass
    except:
        assert True
    else:
        assert False

def test_realize():
    # Get config file data to compare to cell output.
    with open("fixtures/config/getConfig.yaml", "r", encoding="utf-8") as f:
        config1_str = f.read().rstrip()
        config1_dict = yaml.safe_load(config1_str)
    with open("fixtures/config/update-template.nml", "r", encoding="utf-8") as f:
        update_config_str = f.read().rstrip()
    with open("fixtures/config/keys-config.yaml", "r", encoding="utf-8") as f:
        keys_config_str = f.read().rstrip()
        keys_config_dict = yaml.safe_load(keys_config_str)
    with testbook("config.ipynb", execute=non_err_cells) as tb:
        # Ensure that cell output text matches expectations.
        assert tb.cell_output_text(21) == str(config1_dict)
        assert tb.cell_output_text(23) == config1_str
        assert tb.cell_output_text(25) == str(config1_dict)
        for item in config1_dict.items():
            assert item[0] + "=" + item[1] in tb.cell_output_text(27)
        assert tb.cell_output_text(29) == update_config_str
        assert "'sender_id': '{{ id }}'" in tb.cell_output_text(31) \
               and "'message': 'Salutations, Mars!'" in tb.cell_output_text(31) \
               and "'sent': True" in tb.cell_output_text(31)
        assert "sender_id = '{{ id }}'" in tb.cell_output_text(33) \
               and "message = 'Salutations, Mars!'" in tb.cell_output_text(33) \
               and "sent = .true." in tb.cell_output_text(33)
        assert tb.cell_output_text(35) == keys_config_str
        assert 'message: Good morning, Venus!' in tb.cell_output_text(37)
        assert tb.cell_output_text(39) == update_config_str
        assert 'message.sender_id: {{ id }}' in tb.cell_output_text(41) and \
               'message.message: {{ greeting }}, {{ recipient }}!' in tb.cell_output_text(41)
        assert tb.cell_output_text(43) == update_config_str
        assert "'sender_id': '321'" in tb.cell_output_text(47) \
               and "'message': 'Salutations, Mars!'" in tb.cell_output_text(47) \
               and "'sent': True" in tb.cell_output_text(47)
        assert "sender_id = '321'" in tb.cell_output_text(49) \
               and "message = 'Salutations, Mars!'" in tb.cell_output_text(49) \
               and "sent = .true." in tb.cell_output_text(49)

def test_realize_errs():
    try:
        with testbook("config.ipynb", execute=[1,45]):
            pass
    except:
        assert True
    else:
        assert False

def test_realize_to_dict():
    with open("fixtures/config/getConfig.yaml", "r", encoding="utf-8") as f:
        config1_str = f.read().rstrip()
        config1_dict = yaml.safe_load(config1_str)
    with testbook("config.ipynb", execute=non_err_cells) as tb:
        assert tb.cell_output_text(53) == config1_str
        assert "'id': '456'" in tb.cell_output_text(55) and \
               "'greeting': 'Hello'" in tb.cell_output_text(55) and \
               "'recipient': 'World'" in tb.cell_output_text(55)
