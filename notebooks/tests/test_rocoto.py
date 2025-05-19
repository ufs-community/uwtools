from pathlib import Path

from pytest import fixture
from testbook import testbook

base = Path("fixtures/rocoto")


@fixture(scope="module")
def tb():
    with testbook("rocoto.ipynb", execute=True) as tb:
        yield tb


def test_rocoto_building_simple_workflow(load, tb):
    assert tb.cell_output_text(5) == load(base / "simple-workflow.yaml")
    valid_out = (
        "INFO Schema validation succeeded for Rocoto config",
        "INFO Schema validation succeeded for Rocoto XML",
        "True",
    )
    assert all(x in tb.cell_output_text(7) for x in valid_out)
    assert tb.cell_output_text(9) == load("tmp/simple-workflow.xml")
    assert tb.cell_output_text(11) == load(base / "err-workflow.yaml")
    err_out = (
        "ERROR 3 schema-validation errors found",
        "ERROR Error at workflow.attrs:",
        "ERROR   'realtime' is a required property",
        "ERROR Error at workflow.tasks.task_greet:",
        "ERROR   'command' is a required property",
        "ERROR Error at workflow:",
        "ERROR   'log' is a required property",
        "YAML validation errors",
    )
    assert all(x in tb.cell_output_text(13) for x in err_out)


def test_rocoto_building_workflows(load, tb):
    assert tb.cell_output_text(15) == load(base / "ent-workflow.yaml")
    assert tb.cell_output_text(17) == load(base / "ent-cs-workflow.yaml")
    valid_out = (
        "INFO Schema validation succeeded for Rocoto config",
        "INFO Schema validation succeeded for Rocoto XML",
        "True",
    )
    assert all(x in tb.cell_output_text(19) for x in valid_out)
    assert tb.cell_output_text(21) == load("tmp/ent-cs-workflow.xml")
    assert tb.cell_output_text(23) == load(base / "tasks-workflow.yaml")
    assert tb.cell_output_text(25) == load(base / "tasks-deps-workflow.yaml")
    assert all(x in tb.cell_output_text(27) for x in valid_out)
    assert tb.cell_output_text(29) == load("tmp/tasks-deps-workflow.xml")
    assert tb.cell_output_text(31) == load(base / "meta-workflow.yaml")
    assert all(x in tb.cell_output_text(33) for x in valid_out)
    assert tb.cell_output_text(35) == load("tmp/meta-workflow.xml")
    assert tb.cell_output_text(37) == load(base / "meta-nested-workflow.yaml")


def test_rocoto_validate(tb):
    simple_xml = (base / "simple-workflow.xml").read_text().rstrip()
    err_xml = (base / "err-workflow.xml").read_text().rstrip()
    assert tb.cell_output_text(41) == simple_xml
    valid_out = ("INFO Schema validation succeeded for Rocoto XML", "True")
    assert all(x in tb.cell_output_text(43) for x in valid_out)
    assert tb.cell_output_text(45) == err_xml
    err_out = (
        "ERROR 4 Rocoto XML validation errors found",
        "Element workflow failed to validate attributes",
        "Expecting an element cycledef, got nothing",
        "Invalid sequence in interleave",
        "Element workflow failed to validate content",
    )
    assert all(x in tb.cell_output_text(47) for x in err_out)
