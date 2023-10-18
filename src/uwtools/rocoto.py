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
from uwtools.types import DefinitePath, OptionalPath
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


def _add_jobname_to_tasks(
    input_yaml: OptionalPath = None,
) -> YAMLConfig:
    """
    Load YAML config and add job names to each defined workflow task.

    :param input_yaml: Path to YAML input file.
    """
    values = YAMLConfig(input_yaml)
    tasks = values["workflow"]["tasks"]
    if isinstance(tasks, dict):
        _add_jobname(tasks)
    return values


def _rocoto_schema_xml() -> DefinitePath:
    """
    The path to the file containing the schema to validate the XML file against.
    """
    with resources.as_file(resources.files("uwtools.resources")) as path:
        return path / "schema_with_metatasks.rng"


def _rocoto_schema_yaml() -> DefinitePath:
    """
    The path to the file containing the schema to validate the YAML file against.
    """
    with resources.as_file(resources.files("uwtools.resources")) as path:
        return path / "rocoto.jsonschema"


def _rocoto_template_xml() -> DefinitePath:
    """
    The path to the file containing the Rocoto workflow document template to render.
    """
    with resources.as_file(resources.files("uwtools.resources")) as path:
        return path / "rocoto.jinja2"


def _write_rocoto_xml(
    config_file: OptionalPath,
    rendered_output: DefinitePath,
) -> None:
    """
    Render the Rocoto workflow defined in the given YAML to XML.

    :param config_file: Path to YAML input file.
    :param rendered_output: Path to write rendered XML file.
    """

    values = _add_jobname_to_tasks(config_file)

    # Render the template.
    template = J2Template(values=values.data, template_path=_rocoto_template_xml())
    template.dump(output_path=str(rendered_output))


# Public functions
def realize_rocoto_xml(
    config_file: OptionalPath,
    rendered_output: DefinitePath,
) -> bool:
    """
    Realize the Rocoto workflow defined in the given YAML as XML. Validate both the YAML input and
    XML output.

    :param config_file: Path to YAML input file.
    :param rendered_output: Path to write rendered XML file.
    """

    # Validate the YAML.
    if uwtools.config.validator.validate_yaml(
        config_file=config_file, schema_file=_rocoto_schema_yaml()
    ):
        _add_jobname_to_tasks(config_file)
        # Render the template to a temporary file.
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            _write_rocoto_xml(
                config_file=config_file,
                rendered_output=temp_file.name,
            )
            # Validate the XML.
            if validate_rocoto_xml(input_xml=temp_file.name):
                # If no issues were detected, save temp file and report success.
                shutil.move(temp_file.name, rendered_output)
                return True
        logging.error("Rocoto validation errors identified in %s", temp_file.name)
        return False
    logging.error("YAML validation errors identified in %s", config_file)
    return False


def validate_rocoto_xml(input_xml: OptionalPath) -> bool:
    """
    Given a rendered XML file, validate it against the Rocoto schema.

    :param input_xml: Path to rendered XML file.
    """

    # Validate the XML.
    with open(_rocoto_schema_xml(), "r", encoding="utf-8") as f:
        schema = etree.RelaxNG(etree.parse(f))
    with readable(input_xml) as f:
        xml = f.read()
    tree = etree.fromstring(bytes(xml, encoding="utf-8"))
    success = schema.validate(tree)

    # Log validation errors.
    errors = str(etree.RelaxNG.error_log).split("\n")
    log_method = logging.error if len(errors) else logging.info
    log_method("%s Rocoto validation error%s found", len(errors), "" if len(errors) == 1 else "s")
    for line in errors:
        logging.error(line)

    return success
