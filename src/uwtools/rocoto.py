"""
Support for creating Rocoto XML workflow documents.
"""

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from lxml import etree
from lxml.etree import Element, SubElement

from uwtools.config.core import YAMLConfig
from uwtools.config.validator import validate_yaml
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.types import OptionalPath
from uwtools.utils.file import readable, resource_pathobj, writable


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

    _, temp_file = tempfile.mkstemp(suffix=".xml")

    _RocotoXML(config_file).dump(temp_file)

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
    with open(resource_pathobj("schema_with_metatasks.rng"), "r", encoding="utf-8") as f:
        schema = etree.RelaxNG(etree.parse(f))
    valid = schema.validate(tree)
    nerr = len(schema.error_log)
    log_method = log.info if valid else log.error
    log_method("%s Rocoto validation error%s found", nerr, "" if nerr == 1 else "s")
    for err in list(schema.error_log):
        log.error(err)
    return valid


class _RocotoXML:
    """
    Generate a Rocoto XML document from a UW YAML config.
    """

    def __init__(self, config_file: OptionalPath = None) -> None:
        self._config_validate(config_file)
        self._config = YAMLConfig(config_file).data
        self._add_workflow(self._config)

    def dump(self, path: OptionalPath = None) -> None:
        """
        Emit Rocoto XML document to file or stdout.

        :param path: Optional path to write XML document to.
        """
        # Tidy the tree, render to a string, fix mangled entities (e.g. "&amp;FOO;" -> "&FOO;"),
        # insert !DOCTYPE block, then write final XML.
        xml = etree.tostring(
            self._tidy(self._root), pretty_print=True, encoding="utf-8", xml_declaration=True
        ).decode()
        xml = re.sub(r"&amp;([^;]+);", r"&\1;", xml)
        xml = self._insert_doctype(xml)
        with writable(path) as f:
            f.write(xml.strip())

    @property
    def _doctype(self) -> Optional[str]:
        """
        Generate the <!DOCTYPE> block with <!ENTITY> definitions.

        :return: The <!DOCTYPE> block if entities are defined, otherwise None.
        """
        if entities := self._config[STR.workflow].get(STR.entities):
            tags = (f'  <!ENTITY {k} "{v}">' for k, v in entities.items())
            return "<!DOCTYPE workflow [\n%s\n]>" % "\n".join(tags)
        return None

    def _config_validate(self, config_file: OptionalPath) -> None:
        """
        Validate the given YAML config.

        :param config_file: Path to the YAML config (defaults to stdin).
        """
        if not validate_yaml(
            config_file=config_file, schema_file=resource_pathobj("rocoto.jsonschema")
        ):
            raise UWConfigError("YAML validation errors identified in %s" % config_file)

    def _add_metatask(self, e: Element, config: dict, taskname: str) -> None:
        """
        Add a <metatask> element to the <workflow>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        :param taskname: The name of the metatask being defined.
        """
        e = SubElement(e, STR.metatask, name=taskname)
        for key, val in config.items():
            tag, taskname = self._tag_name(key)
            if tag == STR.metatask:
                self._add_metatask(e, val, taskname)
            elif tag == STR.task:
                self._add_task(e, val, taskname)
            elif tag == STR.var:
                for name, value in val.items():
                    SubElement(e, STR.var, name=name).text = value

    def _add_task(self, e: Element, config: dict, taskname: str) -> None:
        """
        Add a <task> element to the <workflow>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        :param taskname: The name of the task being defined.
        """
        e = SubElement(e, STR.task, name=taskname)
        self._set_attrs(e, config)
        # These elements are simple enough to not require their own methods:
        for name in (STR.account, STR.command, STR.nodes, STR.walltime):
            if name in config:
                SubElement(e, name).text = config[name]
        # The job name, if unspecified, defaults to the task name.
        SubElement(e, STR.jobname).text = config.get(STR.jobname, taskname)
        # Add any dependencies:
        if STR.dependency in config:
            self._add_task_dependency(e, config[STR.dependency])
        # Add any environment-variable entities:
        for name, value in config.get(STR.envars, {}).items():
            self._add_task_envar(e, name, value)

    def _add_task_dependency(self, e: Element, config: dict) -> None:
        """
        Add a <dependency> element to the <task>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """
        e = SubElement(e, STR.dependency)
        for key, block in config.items():
            tag, _ = self._tag_name(key)
            if tag == STR.taskdep:
                d = SubElement(e, STR.taskdep)
                self._set_attrs(d, block)
            else:
                raise UWConfigError("Unhandled dependency type %s" % tag)

    def _add_task_envar(self, e: Element, name: str, value: str) -> None:
        """
        Add a <envar> element to the <task>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """
        e = SubElement(e, STR.envar)
        SubElement(e, STR.name).text = name
        SubElement(e, STR.value).text = value

    def _add_workflow(self, config: dict) -> None:
        """
        Create the root <workflow> element.

        :param config: Configuration data for this element.
        """
        config, e = config[STR.workflow], Element(STR.workflow)
        self._set_attrs(e, config)
        self._add_workflow_cycledefs(e, config[STR.cycledefs])
        self._add_workflow_log(e, config[STR.log])
        self._add_workflow_tasks(e, config[STR.tasks])
        self._root: Element = e

    def _add_workflow_cycledefs(self, e: Element, config: dict) -> None:
        """
        Add <cycledef> element(s) to the <workflow>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """
        for name, coords in config.items():
            for coord in coords:
                SubElement(e, STR.cycledef, group=name).text = coord

    def _add_workflow_log(self, e: Element, logfile: str) -> None:
        """
        Add <log> element(s) to the <workflow>.

        :param e: The parent element to add the new element to.
        :param logfile: The path to the log file.
        """
        SubElement(e, STR.log).text = logfile

    def _add_workflow_tasks(self, e: Element, config: dict) -> None:
        """
        Add <task> and/or <metatask> element(s) to the <workflow>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for these elements.
        """
        for key, block in config.items():
            tag, name = self._tag_name(key)
            {STR.metatask: self._add_metatask, STR.task: self._add_task}[tag](e, block, name)

    def _insert_doctype(self, xml: str) -> str:
        """
        Insert the <!DOCTYPE> block in a rendered XML document.

        :param xml: The XML document rendered as a string.
        :return: The XML document with the <!DOCTYPE> block inserted.
        """
        lines = xml.split("\n")
        if doctype := self._doctype:
            lines.insert(1, doctype)
        return "\n".join(lines)

    def _set_attrs(self, e: Element, config: dict) -> None:
        """
        Set attributes on an element.

        :param e: The element to set the attributes on.
        :param config: A config containing the attribute definitions.
        """
        for attr, val in config[STR.attrs].items():
            e.set(attr, str(val))

    def _tag_name(self, key: str) -> Tuple[str, str]:
        """
        Split a metadata-bearing key into base tag and metadata.

        :param key: A string of the form "tag_metadata" (or simply STR.tag).
        :return: The base tag and metadata, separated.
        """
        m = re.match(r"^([^_]+)(_(.*))?$", key)
        assert m  # validated config => regex match
        tag, name = m[1], m[3]
        return tag, name

    def _tidy(self, e: Element) -> Element:
        """
        Construct a semantically-equivalent tree with child elements and attributes in sorted order.

        :param e: The element tree to sort.
        :return: A new element tree with child elements and attributes in sorted order.
        """
        # Create a new element named the same as the current element, add the attrs in sorted order,
        # then add the (recursively tidied) children in sorted order.
        tidy_e = Element(e.tag)
        for attr, val in sorted(e.items(), key=lambda x: x[0]):
            tidy_e.set(attr, val)
        tidy_e.text = e.text
        for child in sorted(list(e), key=lambda x: x.tag):
            tidy_e.append(self._tidy(child))
        return tidy_e


@dataclass(frozen=True)
class _STR:
    """
    A lookup map for Rocoto-related strings.
    """

    account: str = "account"
    attrs: str = "attrs"
    command: str = "command"
    cycledef: str = "cycledef"
    cycledefs: str = "cycledefs"
    dependency: str = "dependency"
    entities: str = "entities"
    envar: str = "envar"
    envars: str = "envars"
    jobname: str = "jobname"
    log: str = "log"
    metatask: str = "metatask"
    name: str = "name"
    nodes: str = "nodes"
    tag: str = "tag"
    task: str = "task"
    taskdep: str = "taskdep"
    tasks: str = "tasks"
    value: str = "value"
    var: str = "var"
    walltime: str = "walltime"
    workflow: str = "workflow"


STR = _STR()
