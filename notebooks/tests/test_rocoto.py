from testbook import testbook


def test_building_simple_workflow():
    with open("fixtures/rocoto/simple-workflow.yaml", "r", encoding="utf-8") as f:
        simple_yaml = f.read().rstrip()
    with open("fixtures/rocoto/err-workflow.yaml", "r", encoding="utf-8") as f:
        err_yaml = f.read().rstrip()
    with testbook("rocoto.ipynb", execute=True) as tb:
        with open("tmp/simple-workflow.xml", "r", encoding="utf-8") as f:
            simple_xml = f.read().rstrip()
        assert tb.cell_output_text(5) == simple_yaml
        valid_out = (
            "INFO 0 UW schema-validation errors found",
            "INFO 0 Rocoto validation errors found",
            "True",
        )
        assert all(x in tb.cell_output_text(7) for x in valid_out)
        assert tb.cell_output_text(9) == simple_xml
        assert tb.cell_output_text(11) == err_yaml
        err_out = (
            "ERROR 3 UW schema-validation errors found",
            "ERROR Error at workflow -> attrs:",
            "ERROR   'realtime' is a required property",
            "ERROR Error at workflow -> tasks -> task_greet:",
            "ERROR   'command' is a required property",
            "ERROR Error at workflow:",
            "ERROR   'log' is a required property",
            "YAML validation errors",
        )
        assert all(x in tb.cell_output_text(13) for x in err_out)


def test_building_workflows():
    with open("fixtures/rocoto/ent-workflow.yaml", "r", encoding="utf-8") as f:
        ent_yaml = f.read().rstrip()
    with open("fixtures/rocoto/ent-cs-workflow.yaml", "r", encoding="utf-8") as f:
        ent_cs_yaml = f.read().rstrip()
    with open("fixtures/rocoto/tasks-workflow.yaml", "r", encoding="utf-8") as f:
        tasks_yaml = f.read().rstrip()
    with open("fixtures/rocoto/tasks-deps-workflow.yaml", "r", encoding="utf-8") as f:
        tasks_deps_yaml = f.read().rstrip()
    with open("fixtures/rocoto/meta-workflow.yaml", "r", encoding="utf-8") as f:
        meta_yaml = f.read().rstrip()
    with open("fixtures/rocoto/meta-nested-workflow.yaml", "r", encoding="utf-8") as f:
        meta_nested_yaml = f.read().rstrip()
    with testbook("rocoto.ipynb", execute=True) as tb:
        with open("tmp/ent-cs-workflow.xml", "r", encoding="utf-8") as f:
            ent_cs_xml = f.read().rstrip()
        with open("tmp/tasks-deps-workflow.xml", "r", encoding="utf-8") as f:
            tasks_deps_xml = f.read().rstrip()
        with open("tmp/meta-workflow.xml", "r", encoding="utf-8") as f:
            meta_xml = f.read().rstrip()
        assert tb.cell_output_text(15) == ent_yaml
        assert tb.cell_output_text(17) == ent_cs_yaml
        valid_out = (
            "INFO 0 UW schema-validation errors found",
            "INFO 0 Rocoto validation errors found",
            "True",
        )
        assert all(x in tb.cell_output_text(19) for x in valid_out)
        assert tb.cell_output_text(21) == ent_cs_xml
        assert tb.cell_output_text(23) == tasks_yaml
        assert tb.cell_output_text(25) == tasks_deps_yaml
        assert all(x in tb.cell_output_text(27) for x in valid_out)
        assert tb.cell_output_text(29) == tasks_deps_xml
        assert tb.cell_output_text(31) == meta_yaml
        assert all(x in tb.cell_output_text(33) for x in valid_out)
        assert tb.cell_output_text(35) == meta_xml
        assert tb.cell_output_text(37) == meta_nested_yaml


def test_validate():
    with open("fixtures/rocoto/simple-workflow.xml", "r", encoding="utf-8") as f:
        simple_xml = f.read().rstrip()
    with open("fixtures/rocoto/err-workflow.xml", "r", encoding="utf-8") as f:
        err_xml = f.read().rstrip()
    with testbook("rocoto.ipynb", execute=True) as tb:
        assert tb.cell_output_text(41) == simple_xml
        valid_out = ("INFO 0 Rocoto XML validation errors found", "True")
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
