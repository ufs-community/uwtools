import os

import yaml
from testbook import testbook

def test_get_config():
    config2_str = 'message:\n  greeting: Hi\n  recipient: Earth'
    # Get the config file as text and dict.
    with open("fixtures/config/getConfig.yaml", "r", encoding="utf-8") as f:
        config1_str = f.read().rstrip()
        config1_dict = yaml.safe_load(config1_str)
    with testbook("config.ipynb", execute=range(0,10)) as tb:
        #  Ensure that notebook variables have the correct values
        assert tb.ref("config1") == config1_dict
        assert tb.ref("config2") == yaml.safe_load(config2_str)
        # Ensure that cell output text matches expectations.
        assert tb.cell_output_text(5) == config1_str
        assert tb.cell_output_text(7) == config1_str
        assert tb.cell_output_text(9) == config2_str

def test_realize():
    # Get the config file as text and dict.
    with open("fixtures/config/getConfig.yaml", "r", encoding="utf-8") as f:
        config1_str = f.read().rstrip()
        config1_dict = yaml.safe_load(config1_str)
    with testbook("config.ipynb", execute=range(0,20)) as tb:
        # Ensure that cell output text matches expectations.
        assert tb.cell_output_text(13) == str(config1_dict)
        assert tb.cell_output_text(15) == config1_str
        assert tb.cell_output_text(17) == str(config1_dict)
        for item in config1_dict.items():
            assert item[0] + "=" + item[1] in tb.cell_output_text(19)