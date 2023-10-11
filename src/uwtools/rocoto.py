"""
Support for creating Rocoto XML workflow documents.
"""

import logging

from lxml import etree

import uwtools.config.validator
from uwtools.config.core import YAMLConfig
from uwtools.config.j2template import J2Template

# Private functions


def _add_jobname(tree: dict) -> None:
    """
    Add a "jobname" attribute to each "task" element in the given config tree.

    :param tree: A config tree containing "task" elements..
    """
    for element, subtree in tree.items():
        element_parts = element.split("_", maxsplit=1)
        element_type = element_parts[0]
        if element_type == "task":
            # Use the provided attribute if it is present, otherwise use the name in the key.
            task_name = element_parts[1]
            tree[element]["jobname"] = subtree.get("attrs", {}).get("name") or task_name
        elif element_type == "metatask":
            _add_jobname(subtree)


# Public functions
def realize_rocoto_xml(
    input_yaml: str,
    input_template: str,
    rendered_output: str,
    schema_file: str,
) -> None:  # pragma: no cover
    """
    Main entry point.

    :param input_yaml: Path to YAML input file.
    :param input_template: Path to input template file.
    :param rendered_output: Path to write rendered XML file.
    :param schema_file: Path to schema file.
    """
    values = YAMLConfig(input_yaml)
    tasks = values["tasks"]
    if isinstance(tasks, dict):
        _add_jobname(tasks)

    # Validate the YAML.
    if uwtools.config.validator.validate_yaml(config_file=input_yaml, schema_file=input_template):
        # Render the template.
        write_rocoto_xml(
            input_yaml=input_yaml,
            input_template=str(input_template),
            rendered_output=str(rendered_output),
        )
        # Validate the XML.
        if validate_rocoto_xml(input_xml=str(rendered_output), schema_file=str(schema_file)):
            logging.info("%s successfully realized.", rendered_output)
        else:
            logging.error("Rocoto validation errors identified in %s", rendered_output)
    else:
        logging.error("YAML validation errors identified in %s", input_yaml)


def validate_rocoto_xml(input_xml: str, schema_file: str) -> bool:
    """
    Main entry point.

    :param input_XML: Path to rendered XML file.
    :param schema_file: Path to schema file.
    """

    # Validate the XML.
    with open(schema_file, "r", encoding="utf-8") as f:
        schema = etree.RelaxNG(etree.parse(f))
    tree = etree.parse(input_xml)
    return schema.validate(tree)


def write_rocoto_xml(input_yaml: str, input_template: str, rendered_output: str) -> None:
    """
    Main entry point.

    :param input_yaml: Path to YAML input file.
    :param input_template: Path to input template file.
    :param rendered_output: Path to write rendered XML file.
    """
    values = YAMLConfig(input_yaml)
    tasks = values["tasks"]
    if isinstance(tasks, dict):
        _add_jobname(tasks)

    # Render the template.
    template = J2Template(values=values.data, template_path=input_template)
    template.dump(output_path=rendered_output)
