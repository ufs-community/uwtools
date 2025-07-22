"""
Support for creating Rocoto XML workflow documents.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from itertools import chain
from math import log10
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING, Any

from lxml import etree
from lxml.builder import E  # type: ignore[import-not-found]
from lxml.etree import Element, SubElement, _Element

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.validator import validate_external as validate_yaml
from uwtools.exceptions import UWConfigError, UWError
from uwtools.logging import log
from uwtools.utils.file import readable, resource_path, writable
from uwtools.utils.processing import run_shell_cmd

if TYPE_CHECKING:
    from datetime import datetime


DEFAULT_ITERATION_RATE = 10


def realize(config: YAMLConfig | Path | None, output_file: Path | None = None) -> str:
    """
    Realize the Rocoto workflow defined in the given YAML as XML, validating both the YAML input and
    XML output.

    :param config: Path to YAML input file (None => read stdin), or YAMLConfig object.
    :param output_file: Path to write rendered XML file (None => write to stdout).
    :return: An XML string.
    """
    rxml = _RocotoXML(config)
    xml = str(rxml).strip()
    if not validate_string(xml):
        msg = "Internal error: Invalid Rocoto XML"
        raise UWError(msg)
    with writable(output_file) as f:
        print(xml, file=f)
    return xml


def run(cycle: datetime, database: Path, rate: int, task: str, workflow: Path) -> bool:
    return _RocotoRunner(cycle, database, rate, task, workflow).run()


def validate_file(xml_file: Path | None) -> bool:
    """
    Validate purported Rocoto XML file against its schema.

    :param xml_file: Path to XML file (None => read stdin).
    :return: Did the XML conform to the schema?
    """
    with readable(xml_file) as f:
        return validate_string(xml=f.read())


def validate_string(xml: str) -> bool:
    """
    Validate purported Rocoto XML against its schema.

    :param xml: XML to validate.
    :return: Did the XML conform to the schema?
    """
    tree = etree.fromstring(xml.encode("utf-8"))
    path = resource_path("rocoto/schema_with_metatasks.rng")
    schema = etree.RelaxNG(etree.fromstring(path.read_text()))
    valid: bool = schema.validate(tree)
    if valid:
        log.info("Schema validation succeeded for Rocoto XML")
    else:
        nerr = len(schema.error_log)
        log.error("%s Rocoto XML validation error%s found", nerr, "" if nerr == 1 else "s")
        for err in list(schema.error_log):
            log.error(err)
        log.error("Invalid Rocoto XML:")
        lines = xml.strip().split("\n")
        fmtstr = "%{n}d %s".format(n=int(log10(len(lines))) + 1)
        for n, line in enumerate(lines):
            log.error(fmtstr, n + 1, line)
    return valid


class _RocotoRunner:
    def __init__(self, cycle: datetime, database: Path, rate: int, task: str, workflow: Path):
        self._cycle = cycle
        self._database = database
        self._rate = rate
        self._task = task
        self._workflow = workflow
        self._con: sqlite3.Connection | None = None
        self._cur: sqlite3.Cursor | None = None

    def __del__(self):
        if self._con:
            self._con.close()

    def run(self) -> bool:
        state = self._state
        while state not in self._states["inactive"]:
            if not self._iterate():
                return False
            state = self._state
            if state is None or state in self._states["active"]:
                self._report()
                log.debug("Sleeping %s seconds", self._rate)
                sleep(self._rate)
        return True

    @property
    def _connection(self) -> sqlite3.Connection | None:
        if not self._con:
            if not self._database.is_file():
                return None
            self._con = sqlite3.connect(self._database)
        return self._con

    @property
    def _cursor(self) -> sqlite3.Cursor | None:
        if not self._cur:
            if not (connection := self._connection):
                return None
            self._cur = connection.cursor()
        return self._cur

    def _iterate(self) -> bool:
        log.info("Iterating workflow")
        cmd = "rocotorun -d %s -w %s" % (self._database, self._workflow)
        success, _ = run_shell_cmd(cmd, quiet=True)
        return success

    @property
    def _query_data(self) -> dict:
        return {"taskname": self._task, "cycle": int(self._cycle.timestamp())}

    @property
    def _query_stmt(self) -> str:
        return "select state from jobs where taskname=:taskname and cycle=:cycle"

    def _report(self) -> None:
        cmd = "rocotostat -d %s -w %s" % (self._database, self._workflow)
        if self._database.is_file():
            log.info("Workflow status:")
            _, output = run_shell_cmd(cmd, quiet=True)
            for line in output.strip().split("\n"):
                log.info(line)

    @property
    def _state(self) -> str | None:
        state = None
        if cursor := self._cursor:
            result = cursor.execute(self._query_stmt, self._query_data)
            if row := result.fetchone():
                (state,) = row
                log.info(self._state_msg % state)
                assert state in chain.from_iterable(self._states.values())
        return state

    @property
    def _state_msg(self) -> str:
        return f"Rocoto task '{self._task}' for cycle {self._cycle}: %s"

    @property
    def _states(self) -> dict:
        return {
            "active": ["QUEUED", "RUNNING"],
            "inactive": ["COMPLETE", "DEAD", "ERROR", "STUCK", "SUCCEEDED"],
            "transient": ["CREATED", "DYING", "STALLED", "SUBMITTING"],
        }


class _RocotoXML:
    """
    Generate a Rocoto XML document from a YAML config.
    """

    def __init__(self, config: dict | YAMLConfig | Path | None = None) -> None:
        self._config_validate(config)
        cfgobj = config if isinstance(config, YAMLConfig) else YAMLConfig(config)
        self._config = cfgobj.data
        self._add_workflow(self._config)

    def __str__(self) -> str:
        # Render the tree to a string, fix mangled entities (e.g. "&amp;FOO;" -> "&FOO;"), insert
        # !DOCTYPE block, then write final XML.
        xml = etree.tostring(
            self._root, pretty_print=True, encoding="utf-8", xml_declaration=True
        ).decode()
        xml = re.sub(r"&amp;([^&]+;)", r"&\1", xml)
        return self._insert_doctype(xml)

    def dump(self, path: Path | None = None) -> None:
        """
        Emit Rocoto XML document to file or stdout.

        :param path: Path to write XML document to (None => write to stdout).
        """
        with writable(path) as f:
            f.write(str(self).strip())

    def _add_compound_time_string(self, e: _Element, config: Any, tag: str) -> _Element:
        """
        Add to the given element a child element possibly containing a <cyclestr>.

        :param e: The element to add the child element to.
        :param config: Configuration data for the child element.
        :param tag: Name of child element to add.
        :return: The child element.
        """
        config = config if isinstance(config, list) else [config]
        cyclestr = lambda x: E.cyclestr(x["cyclestr"]["value"], **x["cyclestr"].get("attrs", {}))
        items = [cyclestr(x) if isinstance(x, dict) else str(x) for x in [tag, *config]]
        child: _Element = E(*items)
        e.append(child)
        return child

    def _add_metatask(self, e: _Element, config: dict, name_attr: str) -> None:
        """
        Add a <metatask> element to the <workflow>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        :param name_attr: XML name attribute for element.
        """
        e = SubElement(e, STR.metatask, name=name_attr)
        self._set_attrs(e, config)
        for key, val in config.items():
            tag, name = self._tag_name(key)
            if tag == STR.metatask:
                self._add_metatask(e, val, name)
            elif tag == STR.task:
                self._add_task(e, val, name)
            elif tag == STR.var:
                for varname, value in val.items():
                    SubElement(e, STR.var, name=varname).text = value

    def _add_task(self, e: _Element, config: dict, name_attr: str) -> None:
        """
        Add a <task> element to the <workflow>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        :param name_attr: XML name attribute for element.
        """
        e = SubElement(e, STR.task, name=name_attr)
        self._set_attrs(e, config)
        config = self._set_and_render_jobname(config, name_attr)
        for tag in (
            STR.account,
            STR.cores,
            STR.exclusive,
            STR.memory,
            STR.nodes,
            STR.nodesize,
            STR.partition,
            STR.queue,
            STR.rewind,
            STR.shared,
            STR.walltime,
        ):
            if tag in config:
                SubElement(e, tag).text = str(config[tag])
        for tag in (
            STR.command,
            STR.deadline,
            STR.jobname,
            STR.join,
            STR.native,
            STR.stderr,
            STR.stdout,
        ):
            if tag in config:
                self._add_compound_time_string(e, config[tag], tag)
        for name, value in config.get(STR.envars, {}).items():
            self._add_task_envar(e, name, value)
        if STR.dependency in config:
            self._add_task_dependency(e, config[STR.dependency])

    def _add_task_dependency(self, e: _Element, config: dict) -> None:
        """
        Add a <dependency> element to the <task>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """
        e = SubElement(e, STR.dependency)
        for tag, subconfig in config.items():
            self._add_task_dependency_child(e, subconfig, tag)

    def _add_task_dependency_child(self, e: _Element, config: dict, tag: str) -> None:
        """
        Add an operator/operand element to parent element.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        :param tag: Name of new element to add.
        """
        tag, name = self._tag_name(tag)
        if tag in (STR.and_, STR.nand, STR.nor, STR.not_, STR.or_, STR.xor):
            e = SubElement(e, tag)
            for subtag, subconfig in config.items():
                self._add_task_dependency_child(e, subconfig, subtag)
        elif tag in (STR.streq, STR.strneq):
            self._add_task_dependency_strequality(e, config, tag)
        elif tag == STR.sh:
            self._add_task_dependency_sh(e, config, name)
        elif tag == STR.datadep:
            self._add_task_dependency_datadep(e, config)
        elif tag == STR.taskdep:
            self._add_task_dependency_taskdep(e, config)
        elif tag == STR.metataskdep:
            self._add_task_dependency_metataskdep(e, config)
        elif tag == STR.taskvalid:
            self._add_task_dependency_taskvalid(e, config)
        elif tag == STR.timedep:
            self._add_task_dependency_timedep(e, config)
        else:
            msg = "Unhandled dependency type %s" % tag
            raise UWConfigError(msg)

    def _add_task_dependency_datadep(self, e: _Element, config: dict) -> None:
        """
        Add a <datadep> element to the <dependency>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """
        e = self._add_compound_time_string(e, config[STR.value], STR.datadep)
        self._set_attrs(e, config)

    def _add_task_dependency_metataskdep(self, e: _Element, config: dict) -> None:
        """
        Add a <metataskdep> element to the <dependency>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """
        self._set_attrs(SubElement(e, STR.metataskdep), config)

    def _add_task_dependency_sh(
        self, e: _Element, config: dict, name_attr: str | None = None
    ) -> None:
        """
        :param e: The parent element to add the new element to.
        :param config: Configuration data for the tag.
        :param name_attr: XML name attribute for element.
        """
        e = self._add_compound_time_string(e, config[STR.command], STR.sh)
        config[STR.attrs] = config.get(STR.attrs, {})
        if name_attr:
            config[STR.attrs][STR.name] = name_attr
        self._set_attrs(e, config)

    def _add_task_dependency_strequality(self, e: _Element, config: dict, tag: str) -> None:
        """
        :param e: The parent element to add the new element to.
        :param config: Configuration data for the tag.
        :param tag: Name of new element to add.
        """
        e = SubElement(e, tag)
        for k, v in config.items():
            self._add_compound_time_string(e, v, k)

    def _add_task_dependency_taskdep(self, e: _Element, config: dict) -> None:
        """
        Add a <taskdep> element to the <dependency>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """
        self._set_attrs(SubElement(e, STR.taskdep), config)

    def _add_task_dependency_taskvalid(self, e: _Element, config: dict) -> None:
        """
        Add a <taskvalid> element to the <dependency>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """
        self._set_attrs(SubElement(e, STR.taskvalid), config)

    def _add_task_dependency_timedep(self, e: _Element, config: dict) -> None:
        """
        Add a <timedep> element to the <dependency>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """
        self._add_compound_time_string(e, config, STR.timedep)

    def _add_task_envar(self, e: _Element, name: str, value: str) -> None:
        """
        Add a <envar> element to the <task>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """
        e = SubElement(e, STR.envar)
        SubElement(e, STR.name).text = name

        self._add_compound_time_string(e, value, STR.value)

    def _add_workflow(self, config: dict) -> None:
        """
        Create the root <workflow> element.

        :param config: Configuration data for this element.
        """
        config, e = config[STR.workflow], Element(STR.workflow)
        self._set_attrs(e, config)
        self._add_workflow_cycledef(e, config[STR.cycledef])
        self._add_workflow_log(e, config)
        self._add_workflow_tasks(e, config[STR.tasks])
        self._root: _Element = e

    def _add_workflow_cycledef(self, e: _Element, config: list[dict]) -> None:
        """
        Add <cycledef> element(s) to the <workflow>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for this element.
        """
        for item in config:
            cycledef = SubElement(e, STR.cycledef)
            cycledef.text = item["spec"]
            self._set_attrs(cycledef, item)

    def _add_workflow_log(self, e: _Element, config: dict) -> None:
        """
        Add <log> element(s) to the <workflow>.

        :param e: The parent element to add the new element to.
        :param logfile: The path to the log file.
        """
        tag = STR.log
        e = self._add_compound_time_string(e, config[tag][STR.value], tag)
        self._set_attrs(e, config[tag])

    def _add_workflow_tasks(self, e: _Element, config: dict) -> None:
        """
        Add <task> and/or <metatask> element(s) to the <workflow>.

        :param e: The parent element to add the new element to.
        :param config: Configuration data for these elements.
        """
        for key, subconfig in config.items():
            tag, name = self._tag_name(key)
            {STR.metatask: self._add_metatask, STR.task: self._add_task}[tag](e, subconfig, name)

    def _config_validate(self, config: dict | Path | YAMLConfig | None = None) -> None:
        """
        Validate the given YAML config.

        :param config: YAMLConfig object or path to YAML file (None => read stdin).
        :raises: UWConfigError if config fails validation.
        """
        config_data, config_path = (None, config) if isinstance(config, Path) else (config, None)
        validate_yaml(
            schema_file=resource_path("jsonschema/rocoto.jsonschema"),
            desc="Rocoto config",
            config_data=config_data,
            config_path=config_path,
        )

    @property
    def _doctype(self) -> str | None:
        """
        The <!DOCTYPE> block with <!ENTITY> definitions.

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
        :return: The updated dict with all jobname entries rendered.
        """
        if STR.jobname not in config:
            config[STR.jobname] = taskname
        cfg = YAMLConfig(config=config)
        cfg.dereference()
        return cfg.data

    def _set_attrs(self, e: _Element, config: dict) -> None:
        """
        Set attributes on an element.

        :param e: The element to set the attributes on.
        :param config: A config containing the attribute definitions.
        """
        for attr, val in config.get(STR.attrs, {}).items():
            e.set(attr, str(val))

    def _tag_name(self, key: str) -> tuple[str, str]:
        """
        Return the tag and metadata extracted from a metadata-bearing key.

        :param key: A string of the form "<tag>_<metadata>" (or simply STR.<tag>).
        :return: Tag and name of key.
        """
        # For example, key "task_foo_bar" will be split into tag "task" and name "foo_bar".
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
    cyclestr: str = "cyclestr"
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
    metataskdep: str = "metataskdep"
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
    sh: str = "sh"
    shared: str = "shared"
    stderr: str = "stderr"
    stdout: str = "stdout"
    streq: str = "streq"
    strneq: str = "strneq"
    tag: str = "tag"
    task: str = "task"
    taskdep: str = "taskdep"
    tasks: str = "tasks"
    taskvalid: str = "taskvalid"
    timedep: str = "timedep"
    value: str = "value"
    var: str = "var"
    walltime: str = "walltime"
    workflow: str = "workflow"
    xor: str = "xor"
