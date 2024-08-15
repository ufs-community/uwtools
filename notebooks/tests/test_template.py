import os
import yaml
from testbook import testbook

def test_render():

    rendered_template1 = "fixtures/template/render-complete-1.yaml"
    rendered_template2 = "fixtures/template/render-complete-2.yaml"

    if os.path.exists(rendered_template1):
        os.remove(rendered_template1)
    if os.path.exists(rendered_template2):
        os.remove(rendered_template2)

    with testbook("template.ipynb", execute=True) as tb:

        assert(tb.cell_output_text(5) == 'user:\n  name: {{ first }} {{ last }}\n  favorite_food: {{ food }}')
        assert('INFO   first' in tb.cell_output_text(7) and
            'INFO   food' in tb.cell_output_text(7) and
            'INFO   last' in tb.cell_output_text(7))
        assert(tb.cell_output_text(9) == "first: John\nlast: Doe\nfood: burritos")
        assert(tb.cell_output_text(11) == "user:\n  name: John Doe\n  favorite_food: burritos")
        assert(tb.cell_output_text(13) == "user:\n  name: Jane Doe\n  favorite_food: tamales")

        assert os.path.exists(rendered_template1)
        assert os.path.exists(rendered_template2)

        with open(rendered_template1, "r") as f:
            user_config = yaml.safe_load(f)
        assert user_config["user"] == {"name": "John Doe", "favorite_food": "burritos"}

        with open(rendered_template2, "r") as f:
            user_config = yaml.safe_load(f)
        assert user_config["user"] == {"name": "Jane Doe", "favorite_food": "tamales"}
    
    @testbook("template.ipynb", execute=True)
    def test_render_to_str(tb):

        assert(tb.cell_output_text(13) == "user:\n  name: John Doe\n  favorite_food: burritos")
        assert(tb.ref('result') == "user:\n  name: John Doe\n  favorite_food: burritos")

    def test_translate():

        translated_template = "fixtures/template/translate-complete.yaml"
        
        if os.path.exists(translated_template):
            os.remove(translated_template)

        with testbook("template.ipynb", execute=True) as tb:

            assert(tb.cell_output_text(21) == "flowers:\n  roses: @[ color1 ]\n  violets: @[ color2 ]")
            assert(tb.cell_output_text(23) == "True")
            assert(tb.cell_output_text(25) == "flowers:\n  roses: {{  color1  }}\n  violets: {{  color2  }}")

            assert os.path.exists(translated_template)

            with open(translated_template, "r") as f:
                user_config = yaml.safe_load(f)
                assert user_config["flowers"] == {"roses": "{{  color1  }}", "violets": "{{  color2  }}"}
