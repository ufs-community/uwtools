import os

import yaml
from testbook import testbook


# Run all cells of the example notebook.
@testbook("./example.ipynb", execute=True)
def test_get_yaml_config(tb):

    # Check output text of the cell that prints the YAMLconfig object.
    assert (
        tb.cell_output_text(3)
        == "values:\n  date: 20240105\n  greeting: Good Night\n  recipient: Moon\n  repeat: 2"
    )

    # Extract the config_yaml variable from the notebook and test its values.
    nb_yaml = tb.ref("config_yaml")
    assert nb_yaml["values"] == {
        "date": 20240105,
        "greeting": "Good Night",
        "recipient": "Moon",
        "repeat": 2,
    }


def test_template_render():
    # Remove the rendered file if it exists.
    rendered_path = "./fixtures/rendered_config.yaml"
    if os.path.exists(rendered_path):
        os.remove(rendered_path)

    # Run all cells of the example notebook.
    with testbook("./example.ipynb", execute=True) as tb:

        # Check output text of cells with %%bash cell magics.
        assert (
            tb.cell_output_text(7)
            == "user:\n  name: {{ first }} {{ last }}\n  favorite_food: {{ food }}"
        )
        assert tb.cell_output_text(9) == "first: John\nlast: Doe\nfood: burritos"
        assert tb.cell_output_text(13) == "user:\n  name: John Doe\n  favorite_food: burritos"

        # Check that the rendered file was created in the correct directory.
        assert os.path.exists(rendered_path)

        # Check the contents of the rendered file.
        with open(rendered_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f)
        assert user_config["user"] == {"name": "John Doe", "favorite_food": "burritos"}

    # Clean up the temporary file after the test is run.
    os.remove(rendered_path)


# Run all cells of the example notebook.
@testbook("./example.ipynb", execute=True)
def test_compare(tb):

    # Check output text of the cell prints the correct result
    assert "False" in tb.cell_output_text(21)
    assert "True" in tb.cell_output_text(25)
