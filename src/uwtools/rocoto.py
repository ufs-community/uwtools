"""
Support for creating Rocoto XML workflow documents.
"""

import re
import tempfile
from importlib import resources
from pathlib import Path
from typing import Tuple

from lxml import etree
from lxml.etree import Element, SubElement

from uwtools.config.core import YAMLConfig
from uwtools.config.j2template import J2Template
from uwtools.config.validator import validate_yaml
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import readable, writable

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
    output_file: OptionalPath,
) -> None:
    """
    Render the Rocoto workflow defined in the given YAML to XML.

    :param config_file: Path to YAML input file.
    :param output_file: Path to write rendered XML file.
    """

    values = _add_jobname_to_tasks(config_file)

    # Render the template.
    template = J2Template(values=values.data, template_path=_rocoto_template_xml())
    template.dump(output_path=output_file)


# Public functions


def realize_rocoto_xml(
    config_file: OptionalPath,
    output_file: OptionalPath = None,
) -> bool:
    """
    Realize the Rocoto workflow defined in the given YAML as XML. Validate both the YAML input and
    XML output.

    :param config_file: Path to YAML input file.
    :param output_file: Path to write rendered XML file.
    :return: Did the input and output files conform to theirr schemas?
    """

    if not validate_yaml(config_file=config_file, schema_file=_rocoto_schema_yaml()):
        log.error("YAML validation errors identified in %s", config_file)
        return False

    _, temp_file = tempfile.mkstemp(suffix=".xml")

    _write_rocoto_xml(config_file=config_file, output_file=temp_file)

    if not validate_rocoto_xml(input_xml=temp_file):
        log.error("Rocoto validation errors identified in %s", temp_file)
        return False

    with open(temp_file, "r", encoding="utf-8") as f_in:
        with writable(output_file) as f_out:
            print(f_in.read(), file=f_out)
    Path(temp_file).unlink()
    return True


def validate_rocoto_xml(input_xml: OptionalPath) -> bool:
    """
    Given a rendered XML file, validate it against the Rocoto schema.

    :param input_xml: Path to rendered XML file.
    :return: Did the XML file conform to the schema?
    """
    with readable(input_xml) as f:
        tree = etree.fromstring(bytes(f.read(), encoding="utf-8"))
    with open(_rocoto_schema_xml(), "r", encoding="utf-8") as f:
        schema = etree.RelaxNG(etree.parse(f))
    valid = schema.validate(tree)
    nerr = len(schema.error_log)
    log_method = log.info if valid else log.error
    log_method("%s Rocoto validation error%s found", nerr, "" if nerr == 1 else "s")
    for err in list(schema.error_log):
        log.error(err)
    return valid


# @PM@ Add entity block
# @PM@ Fixup &amp;
# @PM@ Recursive element sort?
# @PM@ Factor out magic strings.
# @PM@ Make some functions methods in RocotoXML?


class RocotoXML:
    """
    ???
    """

    def __init__(self, config_file: OptionalPath = None) -> None:
        self._config_validate(config_file)
        self._add_workflow(YAMLConfig(config_file).data)

    def dump(self, path: OptionalPath = None) -> None:
        """
        ???
        """
        # Render internal etree to string:
        xml = (
            etree.tostring(self._tree, pretty_print=True, encoding="utf-8", xml_declaration=True)
            .decode()
            .strip()
        )
        # Fix mangled entities (e.g. "&amp;FOO;" -> "&FOO;"):
        xml = re.sub(r"&amp;([^;]+);", r"&\1;", xml)
        # Write final XML:
        with writable(path) as f:
            print(xml, file=f)

    def _config_validate(self, config_file: OptionalPath) -> None:
        if not validate_yaml(config_file=config_file, schema_file=_rocoto_schema_yaml()):
            raise UWConfigError("YAML validation errors identified in %s" % config_file)

    def _add_metatask(self, e: Element, config: dict, taskname: str) -> None:
        e = SubElement(e, "metatask", name=taskname)
        for key, val in config.items():
            if key.startswith("metatask"):
                self._add_metatask(e, val, self._tag_name(key)[1])
            elif key.startswith("task"):
                self._add_task(e, val, self._tag_name(key)[1])
            elif key == "var":
                for name, value in val.items():
                    SubElement(e, "var", name=name).text = value

    def _add_task(self, e: Element, config: dict, taskname: str) -> None:
        e = SubElement(e, "task", name=taskname)
        self._set_attrs(e, config)
        # These elements are simple enough to not require their own methods:
        for name in ("account", "command", "nodes", "walltime"):
            if name in config:
                SubElement(e, name).text = config[name]
        # The job name, if unspecified, defaults to the task name.
        SubElement(e, "jobname").text = config.get("jobname", taskname)
        # Add any dependencies:
        if "dependency" in config:
            self._add_task_dependency(e, config["dependency"])
        # Add any environment-variable entities:
        for name, value in config.get("envars", {}).items():
            self._add_task_envvar(e, name, value)

    def _add_task_dependency(self, e: Element, config: dict) -> None:
        e = SubElement(e, "dependency")
        for key, block in config.items():
            tag, _ = self._tag_name(key)
            if tag == "taskdep":
                d = SubElement(e, "taskdep")
                self._set_attrs(d, block)
            else:
                raise UWConfigError("Unhandled dependency type %s" % tag)

    def _add_task_envvar(self, e: Element, name: str, value: str) -> None:
        envvar = SubElement(e, "envvar")
        SubElement(envvar, "name").text = name
        SubElement(envvar, "value").text = value

    def _add_workflow(self, config: dict) -> None:
        name = "workflow"
        config, e = config[name], Element(name)
        self._set_attrs(e, config)
        self._add_workflow_cycledefs(e, config)
        self._add_workflow_log(e, config)
        self._add_workflow_tasks(e, config)
        self._tree = e

    def _add_workflow_cycledefs(self, e: Element, config: dict) -> None:
        for name, coords in config["cycledefs"].items():
            for coord in coords:
                SubElement(e, "cycledef", group=name).text = coord

    def _add_workflow_log(self, e: Element, config: dict) -> None:
        name = "log"
        SubElement(e, name).text = config[name]

    def _add_workflow_tasks(self, e: Element, config: dict) -> None:
        for key, block in config["tasks"].items():
            tag, name = self._tag_name(key)
            {"metatask": self._add_metatask, "task": self._add_task}[tag](e, block, name)

    def _set_attrs(self, e: Element, config: dict) -> None:
        for attr, val in config["attrs"].items():
            e.set(attr, str(val))

    def _tag_name(self, key: str) -> Tuple[str, str]:
        m = re.match(r"^([^_]+)(_(.*))?$", key)
        assert m  # validated config => regex match
        tag, name = m[1], m[3]
        return tag, name
