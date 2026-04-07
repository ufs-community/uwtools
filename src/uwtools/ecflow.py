"""
Support for creating ecFlow suite definitions and ecf scripts.
"""

from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

from ecflow import (  # type: ignore[import-untyped]
    Defs,
    Family,
    Late,
    Node,
    RepeatDate,
    RepeatDateTime,
    RepeatDay,
    RepeatEnumerated,
    RepeatInteger,
    Suite,
    Task,
)

from uwtools.config.formats.base import Config
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.scheduler import JobScheduler
from uwtools.strings import STR

if TYPE_CHECKING:
    from ecflow import NodeContainer


class _ECFlowDef:
    """
    Generate an ecFlow definition file from a YAML config.
    """

    def __init__(self, config: dict | Config | Path | None = None) -> None:
        self._scripts: dict[Path, str] = {}
        cfgobj = config if isinstance(config, Config) else YAMLConfig(config)
        cfgobj = cfgobj.dereference()
        self._config = cfgobj.data[STR.ecflow]
        self._scheduler = self._config.get("scheduler")
        self._d = Defs()
        self._add_workflow_components()

    def __str__(self):
        return self._d.__str__()

    def write_ecf_scripts(self, path: Path | str) -> None:
        """
        The ecf scripts for this workflow.

        :param path: Where to write the ecFlow scripts.
        """

        if not self._scripts:
            log.warning("No scripts are configured for this workflow.")
            return

        for subpath, content in self._scripts.items():
            outpath = path / subpath
            outpath.parent.mkdir(parents=True, exist_ok=True)
            outpath.write_text(content)

    def write_suite_definition(self, path: Path | str) -> None:
        """
        The suite definition artifact.

        :param path: Where to write the suite definition.
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        suite = path / "suite.def"
        suite.write_text(self._d.__str__())

    def _add_workflow_components(self) -> None:
        """
        Add suite(s) and other attributes to the suite definition.
        """
        for key, subconfig in self._config.items():
            tag, name = self._tag_name(key)
            match tag:
                case "extern":
                    for ext in subconfig:
                        self._d.add_extern(ext)
                case "vars":
                    self._d.add_variable(subconfig)
                case "suite":
                    self._add_node(subconfig, Suite(name), self._d)
                case "suites":
                    self._expand_block(subconfig, name, Suite, self._d)

    def _expand_block(
        self,
        config: dict,
        name: str,
        nodetype: Node,
        parent: NodeContainer,
        refs: dict | None = None,
    ) -> None:
        """
        Expand a YAML block over a set of named Nodes.

        :param config: Configuration data for these components.
        :param name: Name of this suite.
        :param nodetype: The class of Node that needs expanding (Suite, Family, or Task)
        :param parent: The parent object to add this set of Nodes to.
        :param refs: Variable/value pairs used in higher-level expand blocks.
        """

        refs = refs if refs is not None else {}
        expand = config["expand"]

        # Check to make sure all lists are the same length.
        try:
            assert list(zip(*expand.values(), strict=True))
        except ValueError as e:
            msg = "All expand variables under %s must be the same length" % (parent.name())
            raise UWConfigError(msg) from e

        # Build up the new blocks in the suite definition.
        primary_variable = list(expand.keys())[0]
        for i in range(len(expand[primary_variable])):
            new_refs = deepcopy(refs)
            new_refs.update({k: v[i] for k, v in expand.items()})
            new_block = YAMLConfig({name: config}).dereference(context={"ec": new_refs})
            new_name = list(new_block.keys())[0]
            args = {
                "config": new_block[new_name],
                "node": nodetype(new_name),
                "parent": parent,
                "refs": new_refs,
            }
            self._add_node(**args)

    def _add_node(  # noqa: C901,PLR0912
        self,
        config: dict,
        node: Node,
        parent: NodeContainer,
        refs: dict | None = None,
    ) -> None:
        """
        Add a suite|family|task (node) to a suite|family (parent).

        :param config: Configuration data for these components.
        :param node: The node to add to the parent.
        :param parent: The parent object to add this node to.
        :param refs: Optional references from expanded nodes from higher in the tree.
        """
        parent.add(node)
        add_items = lambda n, cfg: (n(*args) for args in cfg)
        for key, subconfig in config.items():
            tag, name = self._tag_name(key)
            match tag:
                # Tree buiding cases

                case "family":
                    self._add_node(subconfig, Family(name), node, refs)
                case "families":
                    self._expand_block(subconfig, name, Family, node, refs)
                case "task":
                    self._add_node(subconfig, Task(name), node, refs)
                case "tasks":
                    self._expand_block(subconfig, name, Task, node, refs)

                # Node attribute cases

                case "defstatus":
                    node.add_defstatus(subconfig)
                case "events":
                    for event in subconfig:
                        node.add_event(event)
                case "inlimits":
                    add_items(node.add_inlimit, subconfig)
                case "labels":
                    add_items(node.add_label, subconfig)
                case "late":
                    node.add_late(Late(**subconfig))
                case "limits":
                    add_items(node.add_limit, subconfig)
                case "meters":
                    add_items(node.add_meter, subconfig)
                case "repeat":  # Only one repeat is allowed per node
                    self._add_repeat(subconfig, name, node)
                case "trigger":  # Only one trigger is allowed per node
                    node.add_trigger(subconfig)
                case "vars":  # add_variable accepts a dict
                    node.add_variable(subconfig)
                case "script":
                    self._create_ecf_script(subconfig, node)

    def _add_repeat(self, config: dict, name: str, node: Node) -> None:
        """
        Adds a repeat to a node.

        :param config: Configuration for the repeat.
        :param name: The name of the repeat.
        :param node: The node to add the repeat to.
        """
        match name:
            case "date":
                config["delta"] = config.pop("step", None)
                repeat = RepeatDate
            case "datelist" | "enumerated" | "string":
                repeat = RepeatEnumerated
            case "datetime":
                repeat = RepeatDateTime
            case "day":
                repeat = RepeatDay
            case "int":
                repeat = RepeatInteger
        node.add_repeat(repeat(**config))

    def _create_ecf_script(self, config: dict, task: Task) -> None:
        """
        Write the ecf script for the task to disk.

        :param config: The configuration for the script.
        :param task: The task node.
        """
        scheduler = (
            self._jobscheduler(
                account=config.get("account", ""),
                execution=config.get("execution", ""),
                rundir=config.get("rundir", ""),
            )
            if self._scheduler
            else None
        )
        execution = config[STR.execution]
        cmd = execution.get("jobcmd")
        es = self._ecflowscript(
            execution=[cmd],
            manual=config.get("manual", f"Script to run {task.name()}"),
            envcmds=execution.get("envcmds", []),
            pre_includes=config.get("pre_includes", []),
            post_includes=config.get("post_includes", []),
            scheduler=scheduler,
        )

        path = (
            Path(task.get_abs_node_path().lstrip("/")).parent
            / f"{task.name().split('_', 1)[-1]}.ecf"
        )
        self._scripts[path] = es

    def _ecflowscript(
        self,
        execution: list[str],
        manual: str,
        envcmds: list[str] | None = None,
        envvars: dict[str, str] | None = None,
        pre_includes: list[str] | None = None,
        post_includes: list[str] | None = None,
        scheduler: JobScheduler | None = None,
    ) -> str:
        """
        Return a driver ecFlow script.

        :param execution: Statements to execute.
        :param manual: A brief explanation of purpose of script.
        :param envcmds: Shell commands to set up runtime environment.
        :param envvars: Environment variables to set in runtime environment.
        :param pre_includes: Names of scripts to be included before execution.
        :param post_includes: Names of scripts to be included after execution.
        :param scheduler: A configured job-scheduler object.
        """
        template = """
        {directives}

        model=%MODEL%

        {pre_includes}

        {envcmds}

        {envvars}

        {execution}
        if [[ $? -ne 0 ]]; then
           ecflow_client --msg="***JOB ${ECF_NAME} ERROR RUNNING J-SCRIPT ***"
           ecflow_client --abort
           exit 1
        fi

        {post_includes}

        %manual
        {manual}
        %end
        """
        pre_includes = pre_includes or []
        post_includes = post_includes or []
        directives = scheduler.directives if scheduler else ""
        initcmds = scheduler.initcmds if scheduler else []
        rs = dedent(template).format(
            directives="\n".join(directives),
            envcmds="\n".join(envcmds or []),
            envvars="\n".join([f"export {k}={v}" for k, v in (envvars or {}).items()]),
            execution="\n".join([*initcmds, *execution]),
            manual=manual,
            pre_includes="\n".join([f"%include <{inc}>" for inc in pre_includes]),
            post_includes="\n".join([f"%include <{inc}>" for inc in post_includes]),
            ECF_NAME="ECF_NAME",
        )
        return re.sub(r"\n\n\n+", "\n\n", rs.strip())

    def _jobscheduler(self, account: str, execution: dict, rundir: Path | str) -> JobScheduler:
        """
        Use the execution block to build a JobScheduler object.

        :param account: The user account for the batch system.
        :param execution: The standard UW YAML execution block.
        :param rundir: The directory where the task will run.
        """
        threads = execution.get(STR.threads)
        resources = {
            STR.account: account,
            STR.rundir: rundir,
            STR.scheduler: self._scheduler,
            STR.stdout: "%s.out" % Path(rundir),
            **({STR.threads: threads} if threads else {}),
            **execution.get(STR.batchargs, {}),
        }
        return JobScheduler.get_scheduler(resources)

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
