"""
Support for creating Rocoto XML workflow documents.
"""

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union

from lxml import etree
from lxml.etree import Element, SubElement

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.jinja2 import dereference
from uwtools.config.validator import validate_yaml_config, validate_yaml_file
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

    if not validate_rocoto_xml_file(xml_file=temp_file):
        log.error("Rocoto validation errors identified in %s", temp_file)
        return False

    with open(temp_file, "r", encoding="utf-8") as f_in:
        with writable(output_file) as f_out:
            print(f_in.read(), file=f_out)
    Path(temp_file).unlink()
    return True


def validate_rocoto_xml_file(xml_file: Union[OptionalPath, str]) -> bool:
    """
    Validate purported Rocoto XML file against its schema.

    :param xml: Path to XML file (None => read stdin).
    :return: Did the XML conform to the schema?
    """
    with readable(xml_file) as f:
        return validate_rocoto_xml_string(xml=f.read())


def validate_rocoto_xml_string(xml: str) -> bool:
    """
    Validate purported Rocoto XML against its schema.

    :param xml: XML to validate.
    :return: Did the XML conform to the schema?
    """
    tree = etree.fromstring(xml.encode("utf-8"))
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

    def __init__(self, config: Union[OptionalPath, YAMLConfig] = None) -> None:
        self._config_validate(config)
        cfgobj = config if isinstance(config, YAMLConfig) else YAMLConfig(config)
        self._config = cfgobj.data
        self._add_workflow(self._config)

    def dump(self, path: OptionalPath = None) -> None:
        """
        Emit Rocoto XML document to file or stdout.

        :param path: Optional path to write XML document to.
        """
        # Render the tree to a string, fix mangled entities (e.g. "&amp;FOO;" -> "&FOO;"), insert
        # !DOCTYPE block, then write final XML.
        xml = etree.tostring(
            self._root, pretty_print=True, encoding="utf-8", xml_declaration=True
        ).decode()
        xml = re.sub(r"&amp;([^;]+);", r"&\1;", xml)
        xml = self._insert_doctype(xml)
        with writable(path) as f:
            f.write(xml.strip())

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
        self._set_and_render_jobname(config, taskname)
        for tag in (
            STR.account,
            STR.command,
            STR.cores,
            STR.deadline,
            STR.exclusive,
            STR.jobname,
            STR.join,
            STR.memory,
            STR.native,
            STR.nodes,
            STR.nodesize,
            STR.partition,
            STR.queue,
            STR.rewind,
            STR.shared,
            STR.stderr,
            STR.stdout,
            STR.walltime,
        ):
            if tag in config:
                SubElement(e, tag).text = config[tag]
        for name, value in config.get(STR.envars, {}).items():
            self._add_task_envar(e, name, value)
        if STR.dependency in config:
            self._add_task_dependency(e, config[STR.dependency])

    def _add_task_dependency(self, e: Element, config: dict) -> None:
        """
        Add a <dependency> element to the <task>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """
        operands, operators, strequality = self._dependency_constants
        e = SubElement(e, STR.dependency)

        for tag, block in config.items():
            tag, _ = self._tag_name(tag)
            if tag in operands:
                self._add_task_dependency_operand_operator(e, config={tag: block})
            elif tag in operators:
                self._add_task_dependency_operand_operator(e, config={tag: block})
            elif tag in strequality:
                self._add_task_dependency_strequality(e, block=block, tag=tag)
            else:
                raise UWConfigError("Unhandled dependency type %s" % tag)

    def _add_task_dependency_operand_operator(self, e: Element, config: dict) -> None:
        """
        Add an operand or operator element to the <dependency>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """

        operands, operators, strequality = self._dependency_constants

        for tag, block in config.items():
            tag, _ = self._tag_name(tag)
            if tag in operands:
                self._set_attrs(SubElement(e, tag), block)
            elif tag in operators:
                self._add_task_dependency_operand_operator(SubElement(e, tag), config=block)
            elif tag in strequality:
                self._add_task_dependency_strequality(e, block=block, tag=tag)
            else:
                raise UWConfigError("Unhandled dependency type %s" % tag)

    def _add_task_dependency_strequality(self, e: Element, block: dict, tag: str) -> None:
        """
        :param e: The parent element to add the new element to.
        :param block: Configuration data for the tag.
        :param tag: Configuration new element to add.
        """
        self._set_attrs(SubElement(e, tag), block)

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
        self._add_workflow_cycledef(e, config[STR.cycledef])
        self._add_workflow_log(e, config[STR.log])
        self._add_workflow_tasks(e, config[STR.tasks])
        self._root: Element = e

    def _add_workflow_cycledef(self, e: Element, config: List[dict]) -> None:
        """
        Add <cycledef> element(s) to the <workflow>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """
        for item in config:
            cycledef = SubElement(e, STR.cycledef)
            cycledef.text = item["spec"]
            self._set_attrs(cycledef, item)

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

    def _config_validate(self, config: Union[OptionalPath, YAMLConfig]) -> None:
        """
        Validate the given YAML config.

        :param config_file: Path to YAML config file, or a YAMLConfig object.
        """
        schema_file = resource_pathobj("rocoto.jsonschema")
        if isinstance(config, YAMLConfig):
            ok = validate_yaml_config(schema_file=schema_file, config=config)
        else:
            ok = validate_yaml_file(schema_file=schema_file, config_file=config)
        if not ok:
            raise UWConfigError("YAML validation errors")

    @property
    def _dependency_constants(self) -> Tuple[Tuple, Tuple, Tuple]:
        """
        Returns a tuple for each of the respective dependency types.
        """
        operands = (STR.datadep, STR.taskdep, STR.timedep)
        operators = (STR.and_, STR.nand, STR.nor, STR.not_, STR.or_, STR.xor)
        strequality = (STR.streq, STR.strneq)
        return operands, operators, strequality

    @property
    def _doctype(self) -> Optional[str]:
        """
        Generate the <!DOCTYPE> block with <!ENTITY> definitions.

        :return: The <!DOCTYPE> block if entities are defined, otherwise None.
        """
        if entities := self._config[STR.workflow].get(STR.entities):
            tags = (f'  <!ENTITY {key} "{val}">' for key, val in entities.items())
            return "<!DOCTYPE workflow [\n%s\n]>" % "\n".join(tags)
        return None

    def _insert_doctype(self, xml: str) -> str:
        """
        Return the given XML document with an Inserted <!DOCTYPE> block.

        :param xml: The XML document rendered as a string.
        """
        lines = xml.split("\n")
        if doctype := self._doctype:
            lines.insert(1, doctype)
        return "\n".join(lines)

    def _set_and_render_jobname(self, config: dict, taskname: str) -> dict:
        """
        In the given config, ensure 'jobname' is set, then render {{ jobname }}.

        :param config: Configuration data for this element.
        :param taskname: The name of the task being defined.
        """
        if STR.jobname not in config:
            config[STR.jobname] = taskname
        new = dereference(val=config, context={STR.jobname: config[STR.jobname]})
        assert isinstance(new, dict)
        return new

    def _set_attrs(self, e: Element, config: dict) -> None:
        """
        Set attributes on an element.

        :param e: The element to set the attributes on.
        :param config: A config containing the attribute definitions.
        """
        for attr, val in config.get(STR.attrs, {}).items():
            e.set(attr, str(val))

    def _tag_name(self, key: str) -> Tuple[str, str]:
        """
        Return the tag and metadata extracted from a metadata-bearing key.

        :param key: A string of the form "tag_metadata" (or simply STR.tag).
        """
        # For example, key "task_foo"bar" will be split into tag "task" and name "foo_bar".
        parts = key.split("_")
        tag = parts[0]
        name = "_".join(parts[1:]) if parts[1:] else ""
        return tag, name


@dataclass(frozen=True)
class STR:
    """
    A lookup map for Rocoto-related strings.
    """

    account: str = "account"
    and_: str = "and"
    attrs: str = "attrs"
    command: str = "command"
    cores: str = "cores"
    cycledef: str = "cycledef"
    cycledefs: str = "cycledefs"
    datadep: str = "datadep"
    deadline: str = "deadline"
    dependency: str = "dependency"
    entities: str = "entities"
    envar: str = "envar"
    envars: str = "envars"
    exclusive: str = "exclusive"
    jobname: str = "jobname"
    join: str = "join"
    log: str = "log"
    memory: str = "memory"
    metatask: str = "metatask"
    name: str = "name"
    nand: str = "nand"
    native: str = "native"
    nodes: str = "nodes"
    nodesize: str = "nodesize"
    nor: str = "nor"
    not_: str = "not"
    or_: str = "or"
    partition: str = "partition"
    queue: str = "queue"
    rewind: str = "rewind"
    shared: str = "shared"
    stderr: str = "stderr"
    stdout: str = "stdout"
    streq: str = "streq"
    strneq: str = "strneq"
    tag: str = "tag"
    task: str = "task"
    taskdep: str = "taskdep"
    tasks: str = "tasks"
    timedep: str = "timedep"
    value: str = "value"
    var: str = "var"
    walltime: str = "walltime"
    workflow: str = "workflow"
    xor: str = "xor"
