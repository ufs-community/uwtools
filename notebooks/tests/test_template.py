from glob import glob
from pathlib import Path

import yaml
from pytest import fixture
from testbook import testbook

base = Path("fixtures/template")


@fixture(scope="module")
def tb():
    for p in glob(str(base / "complete-*")):
        Path(p).unlink()
    with testbook("template.ipynb", execute=True) as tb:
        yield tb


def test_template_render(load, tb):
    rend_temp_str1 = load(base / "complete-render-1.yaml")
    temp_yaml1 = yaml.safe_load(rend_temp_str1)
    assert temp_yaml1["user"] == {"name": "John Doe", "favorite_food": "burritos"}
    rend_temp_str2 = load(base / "complete-render-2.yaml")
    temp_yaml2 = yaml.safe_load(rend_temp_str2)
    assert temp_yaml2["user"] == {"name": "Jane Doe", "favorite_food": "tamales"}
    assert tb.cell_output_text(5) == load(base / "render-template.yaml")
    assert (
        "INFO   first" in tb.cell_output_text(7)
        and "INFO   food" in tb.cell_output_text(7)
        and "INFO   last" in tb.cell_output_text(7)
    )
    assert tb.cell_output_text(9) == load(base / "render-values.yaml")
    assert tb.cell_output_text(11) == rend_temp_str1
    assert tb.cell_output_text(13) == rend_temp_str2
    assert rend_temp_str1 in tb.cell_output_text(15) and rend_temp_str2 in tb.cell_output_text(15)


def test_template_render_to_str(tb):
    rend_temp_str = "user:\n  name: John Doe\n  favorite_food: burritos"
    assert tb.ref("result") == rend_temp_str
    assert tb.cell_output_text(19) == rend_temp_str


def test_template_translate(load, tb):
    assert tb.cell_output_text(23) == load(base / "translate-template.yaml")
    assert tb.cell_output_text(25) == "True"
    assert tb.cell_output_text(27) == load(base / "complete-translate.yaml")
