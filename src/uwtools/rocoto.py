"""
Support for creating Rocoto XML workflow documents.
"""

import logging
from importlib import resources

from lxml import etree

import uwtools.config.validator
from uwtools.config.core import YAMLConfig
from uwtools.config.j2template import J2Template
from uwtools.types import OptionalPath
from uwtools.utils.file import readable

# Private functions


def _add_jobname(tree: dict) -> None:
    """
    Add a "jobname" attribute to each "task" element in the given config tree.

    :param tree: A config tree containing "task" elements.
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


def _add_tasks(
    input_yaml: OptionalPath = None,
) -> None:
    """
    Define "task" elements in the given config tree and request a "jobname" for each.

    :param input_yaml: Path to YAML input file.
    """
    values = YAMLConfig(input_yaml)
    tasks = values["tasks"]
    if isinstance(tasks, dict):
        _add_jobname(tasks)


# Public functions
def realize_rocoto_xml(
    input_yaml: OptionalPath = None,
    rendered_output: OptionalPath = None,
) -> bool:  # pragma: no cover
    """
    Realize the given YAML file to XML, using fixed Rocoto RelaxNG schema templates. Validate both
    the YAML and the XML. External functions should call this function.

    :param input_yaml: Path to YAML input file.
    :param input_template: Path to input template file.
    :param rendered_output: Path to write rendered XML file.
    :param schema_file: Path to schema file.
    """

    _add_tasks(input_yaml)

    rocoto_schema = _rocoto_schema()
    rocoto_template = _rocoto_template()

    # Validate the YAML.
    if uwtools.config.validator.validate_yaml(config_file=input_yaml, schema_file=rocoto_schema):
        # Render the template.
        write_rocoto_xml(
            input_yaml=input_yaml,
            input_template=rocoto_template,
            rendered_output=rendered_output,
        )
        # Validate the XML.
        if validate_rocoto_xml(input_xml=rendered_output, schema_file=rocoto_template):
            # If no issues were detected, report success.
            return True
        logging.error("Rocoto validation errors identified in %s", rendered_output)
        return False
    logging.error("YAML validation errors identified in %s", input_yaml)
    return False


def _rocoto_template() -> str:
    """
    The path to the file containing the template to validate the config file against.
    """
    with resources.as_file(resources.files("uwtools.resources")) as path:
        return (path / "rocoto.jinja2").as_posix()


def _rocoto_schema() -> str:
    """
    The path to the file containing the schema to validate the XML file against.
    """
    with resources.as_file(resources.files("uwtools.resources")) as path:
        return (path / "rocoto.jsonschema").as_posix()


def validate_rocoto_xml(input_xml: OptionalPath = None, schema_file: OptionalPath = None) -> bool:
    """
    Given a rendered XML file, validate it against the Rocoto schema.

    :param input_XML: Path to rendered XML file.
    :param schema_file: Path to schema file.
    """

    # Validate the XML.
    with readable(schema_file) as f:
        schema = etree.RelaxNG(etree.parse(f))
    tree = etree.parse(input_xml)
    success = schema.validate(tree)

    # Store validation errors in the main log.
    errors = str(etree.RelaxNG.error_log).split("\n")
    log_method = logging.debug if len(errors) else logging.info
    log_method("%s Rocoto validation error%s found", len(errors), "" if len(errors) == 1 else "s")
    for line in errors:
        logging.debug(line)

    return success


def write_rocoto_xml(
    input_yaml: OptionalPath = None,
    input_template: OptionalPath = None,
    rendered_output: OptionalPath = None,
) -> None:
    """
    Main entry point. Render the given YAML file to XML using the given template.

    :param input_yaml: Path to YAML input file.
    :param input_template: Path to input template file.
    :param rendered_output: Path to write rendered XML file.
    """

    _add_tasks(input_yaml)

    # Render the template.
    template = J2Template(values=YAMLConfig(input_yaml).data, template_path=str(input_template))
    template.dump(output_path=str(rendered_output))
