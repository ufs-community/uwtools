import os

import yaml
from testbook import testbook


def test_render():

    template = "fixtures/template/render-template.yaml"
    values = "fixtures/template/render-values.yaml"
    rendered_template1 = "fixtures/template/render-complete-1.yaml"
    rendered_template2 = "fixtures/template/render-complete-2.yaml"

    for file in rendered_template1, rendered_template2:
        if os.path.exists(file):
            os.remove(file)

    with open(template, "r", encoding="utf-8") as f:
        template_str = f.read().rstrip()
    with open(values, "r", encoding="utf-8") as f:
        values_str = f.read().rstrip()

    with testbook("template.ipynb", execute=True) as tb:

        with open(rendered_template1, "r", encoding="utf-8") as f:
            rend_temp_str1 = f.read().rstrip()
            temp_yaml1 = yaml.safe_load(rend_temp_str1)
        assert temp_yaml1["user"] == {"name": "John Doe", "favorite_food": "burritos"}

        with open(rendered_template2, "r", encoding="utf-8") as f:
            rend_temp_str2 = f.read().rstrip()
            temp_yaml2 = yaml.safe_load(rend_temp_str2)
        assert temp_yaml2["user"] == {"name": "Jane Doe", "favorite_food": "tamales"}

        assert tb.cell_output_text(5) == template_str
        assert (
            "INFO   first" in tb.cell_output_text(7)
            and "INFO   food" in tb.cell_output_text(7)
            and "INFO   last" in tb.cell_output_text(7)
        )
        assert tb.cell_output_text(9) == values_str
        assert tb.cell_output_text(11) == rend_temp_str1
        assert tb.cell_output_text(13) == rend_temp_str2
        assert rend_temp_str1 in tb.cell_output_text(15) and rend_temp_str2 in tb.cell_output_text(
            15
        )


@testbook("template.ipynb", execute=True)
def test_render_to_str(tb):

    rend_temp_str = "user:\n  name: John Doe\n  favorite_food: burritos"
    assert tb.ref("result") == rend_temp_str
    assert tb.cell_output_text(19) == rend_temp_str


def test_translate():

    atparse_template = "fixtures/template/translate-template.yaml"
    translated_template = "fixtures/template/translate-complete.yaml"

    if os.path.exists(translated_template):
        os.remove(translated_template)

    with open(atparse_template, "r", encoding="utf-8") as f:
        atparse_str = f.read().rstrip()

    with testbook("template.ipynb", execute=True) as tb:

        with open(translated_template, "r", encoding="utf-8") as f:
            translated_str = f.read().rstrip()

        assert tb.cell_output_text(23) == atparse_str
        assert tb.cell_output_text(25) == "True"
        assert tb.cell_output_text(27) == translated_str
