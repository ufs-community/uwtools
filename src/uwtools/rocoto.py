"""
Support for creating Rocoto XML workflow documents.
"""

import logging
import shutil
import tempfile
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
    tasks = values["workflow"]["tasks"]
    if isinstance(tasks, dict):
        _add_jobname(tasks)


def _rocoto_schema() -> str:
    """
    The path to the file containing the schema to validate the XML file against.
    """
    with resources.as_file(resources.files("uwtools.resources")) as path:
        return (path / "rocoto.jsonschema").as_posix()


def _rocoto_template() -> str:
    """
    The path to the file containing the Rocoto workflow document template to render.
    """
    with resources.as_file(resources.files("uwtools.resources")) as path:
        # return (path / "rocoto.jinja2").as_posix()
        return (path / "schema_with_metatasks.rng").as_posix()


# Public functions
def realize_rocoto_xml(
    config_file: OptionalPath = None,
    rendered_output: OptionalPath = None,
) -> bool:
    """
    Realize the given YAML file to XML, using the Rocoto RelaxNG schema. Validate both the YAML and
    the XML.

    :param input_yaml: Path to YAML input file.
    :param rendered_output: Path to write rendered XML file.
    """

    rocoto_schema = _rocoto_schema()

    # Validate the YAML.
    if uwtools.config.validator.validate_yaml(config_file=config_file, schema_file=rocoto_schema):
        _add_tasks(config_file)
        # Render the template to a temporary file.
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            write_rocoto_xml(
                config_file=config_file,
                rendered_output=temp_file.name,
            )
            # Validate the XML.
            if validate_rocoto_xml(input_xml=temp_file.name):
                # If no issues were detected, save temp file and report success.
                shutil.move(temp_file.name, str(rendered_output))
                return True
        logging.error("Rocoto validation errors identified in %s", temp_file.name)
        return False
    logging.error("YAML validation errors identified in %s", config_file)
    return False


def validate_rocoto_xml(input_xml: OptionalPath = None) -> bool:
    """
    Given a rendered XML file, validate it against the Rocoto schema.

    :param input_XML: Path to rendered XML file.
    """
    rocoto_template = _rocoto_template()

    # Validate the XML.
    with readable(rocoto_template) as f:
        schema = etree.RelaxNG(etree.parse(f))
    tree = etree.parse(input_xml)
    success = schema.validate(tree)

    # Store validation errors in the main log.
    errors = str(etree.RelaxNG.error_log).split("\n")
    log_method = logging.error if len(errors) else logging.info
    log_method("%s Rocoto validation error%s found", len(errors), "" if len(errors) == 1 else "s")
    for line in errors:
        logging.error(line)

    return success


def write_rocoto_xml(
    config_file: OptionalPath = None,
    rendered_output: OptionalPath = None,
) -> None:
    """
    Render the given YAML file to XML using the given template.

    :param config_file: Path to YAML input file.
    :param rendered_output: Path to write rendered XML file.
    """

    rocoto_template = _rocoto_template()
    _add_tasks(config_file)

    # Render the template.
    template = J2Template(values=YAMLConfig(config_file).data, template_path=str(rocoto_template))
    template.dump(output_path=str(rendered_output))
