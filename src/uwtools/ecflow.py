from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import ecflow as ec
from ecflow import Defs, Family, Suite, Task


from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.tools import walk_key_path
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.scheduler import JobScheduler
from uwtools.strings import STR

if TYPE_CHECKING:
    from ecflow import NodeContainer


class _ECConstant:
    def __init__(self, value: str):
        self.val = value

    def __getattr__(self, name: str):
        def method(*args, **kwargs):  # noqa: ARG001
            return self.val

        return method

    def __deepcopy__(self, memo: str):
        return self


class _ECFlowDef:
    """
    Generate an ecFlow definition file from a YAML config.
    """

    def __init__(self, config: dict | YAMLConfig | Path | None = None) -> None:
        cfgobj = config if isinstance(config, YAMLConfig) else YAMLConfig(config)
        cfgobj = cfgobj.dereference(
            context={
                "cycle": _ECConstant("%CYCLE%"),
                "timevars": {"fff": "%FHR%"},
            }
        )
        self._config = cfgobj.data
        self._add_workflow(self._config.get(STR.ecflow, self._config))

    def __str__(self):
        return self.d.__str__()

    def _add_workflow(self, config: dict) -> None:
        """
        Create the root Def object.

        :param config: Configuration data for this object.
        """
        self.d = Defs()
        self._add_workflow_components(self.d, config)

    def _add_workflow_components(self, d: Defs, config: dict) -> None:
        """
        Add suite(s) and other attributes to the suite definition.

        :param d: The root of the definition tree.
        :param config: Configuration data for these components.
        """
        for key, subconfig in config.items():
            tag, name = self._tag_name(key)
            match tag:
                case "extern":
                    for ext in subconfig:
                        d.add_extern(ext)
                case "vars":
                    d.add_variable(subconfig)
                case "suite":
                    self._add_node(Suite(name), d, subconfig)
                case "suites":
                    self._expand_block(Suite, d, subconfig, name)

    def _expand_block(
        self,
        nodetype: Node,
        parent: NodeContainer,
        config: dict,
        name: str,
        refs: dict | None = None,
    ) -> None:
        """
        Expand a YAML block over a set of named Nodes.

        :param parent: The parent object to add this set of Nodes to.
        :param config: Configuration data for these components.
        :param name: Name of this suite.
        """
        refs = refs if refs is not None else {}
        expand = config["expand"]

        primary_variable = list(expand.keys())[0]
        # Check to make sure all lists are the same length.
        try:
            for _i in zip(*expand.values(), strict=True):
                pass
        except ValueError:
            log.error("All expand variables under %s must be the same length" % (parent.name()))
            raise

        # Build up the new blocks in the suite definition
        for i in range(len(expand[primary_variable])):
            new_ref = deepcopy(refs)
            new_ref.update({k: v[i] for k, v in expand.items()})
            new_block = YAMLConfig({name: config}).dereference(context={"ec": new_ref})
            new_name = list(new_block.keys())[0]
            args = {
                "node": nodetype(new_name),
                "parent": parent,
                "config": new_block[new_name],
                "refs": new_ref,
            }
            self._add_node(**args)

    def _add_node(
        self,
        node: Node,
        parent: NodeContainer,
        config: dict,
        refs: dict | None = None,
    ) -> None:
        """
        Add a suite|family|task (node) to a suite|family (parent).

        :param node: The node to add to the parent.
        :param parent: The parent object to add this node to.
        :param config: Configuration data for these components.
        :param refs: Optional references from expanded nodes from higher in the tree.
        """
        parent.add(node)
        add_items = lambda m, cfg: (node.m(*args) for args in cfg)
        for key, subconfig in config.items():
            tag, name = self._tag_name(key)
            match tag:
                case "family":
                    self._add_node(Family(name), node, subconfig, refs)
                case "families":
                    self._expand_block(Family, node, subconfig, name, refs)
                case "task":
                    self._add_node(Task(name), node, subconfig, refs)
                case "tasks":
                    self._expand_block(Task, node, subconfig, name, refs)
                case "defstatus":
                    node.add_defstatus(subconfig)
                case "events":
                    for event in subconfig:
                        node.add_event(event)
                case "inlimits":
                    add_items(add_inlimit, subconfig)
                case "meters":
                    add_items(add_meter, subconfig)
                case "labels":
                    add_items(add_label, subconfig)
                case "late":
                    node.add_late(subconfig)
                case "limits":
                    add_items(add_limit, subconfig)
                case "repeat": # Only one repeat is allowed per node
                    self._add_repeat(name, node, subconfig)
                case "trigger": # Only one trigger is allowed per node
                    node.add_trigger(subconfig)
                case "vars": # add_variable accepts a dict
                    node.add_variable(subconfig)
                case "key-path":
                    self._create_ecf_script(node, subconfig)

    def _add_repeat(self, name: str, node: Node, config: dict) -> None:
        """
        Adds a repeat to a node.

        :param node: The node to add the repeat to.
        :param config: Configuration for the repeat.
        """
        """
        YAML:

        repeat:
          variable: myvar

          WITH

          start:
          end:
          step: (optional)

          OR

          step:

          OR

          list:
        """
        match name:
            case "date":
                config["delta"] = config.pop("step", None)
                node.add_repeat(RepeatDate(**config))
            case "datetime":
                node.add_repeat(RepeatDateTime(**config))
            case "int":
                node.add_repeat(RepeatInteger(**config))
            case "day":
                node.add_repeat(RepeatDay(**config))
            case "datelist|enumerated|string":
                node.add_repeat(RepeatEnumerated(**config))

    def _create_ecf_script(self, task: Task, key_path: str) -> None:
        """
        Write the ecf script for the task to disk.
        """
        parent, subsection = key_path.rsplit(".", 1)
        ecf_config, _ = walk_key_path(self._config, parent.split("."))
        scheduler = self._scheduler(ecf_config, subsection)

        execution = ecf_config[subsection][STR.execution]
        cmd = execution.get("jobcmd")
        es = self._ecflowscript(
            envcmds=execution.get("envcmds", []),
            execution=[cmd],
            scheduler=scheduler,
            manual=ecf_config[subsection].get("manual", f"Script to run {subsection}"),
        )
        # Placeholders until the output path for scripts and workflow defs are resolved.
        path = Path(
            ".", Path(task.get_abs_node_path()).parent, f"{task.name().split('_')[-1]}.ecf"
        ).resolve()
        print(f"Will write to {path}")
        print(es)

    def _ecflowscript(
        self,
        execution: list[str],
        manual: str,
        envcmds: list[str] | None = None,
        envvars: dict[str, str] | None = None,
        scheduler: JobScheduler | None = None,
    ) -> str:
        """
        Return a driver ecFlow script.

        :param execution: Statements to execute.
        :param envcmds: Shell commands to set up runtime environment.
        :param envvars: Environment variables to set in runtime environment.
        :param scheduler: A job-scheduler object.
        """
        template = """
        {directives}

        model=%MODEL%

        %include <head.h>
        %include <envir-p1.h>

        {envcmds}

        {envvars}

        {execution}
        if [[ $? -ne 0 ]]; then
           ecflow_client --msg="***JOB ${ECF_NAME} ERROR RUNNING J-SCRIPT ***"
           ecflow_client --abort
           exit 1
        fi

        %include <tail.h>

        %manual
        {manual}
        %end
        """
        directives = scheduler.directives if scheduler else ""
        initcmds = scheduler.initcmds if scheduler else []
        rs = dedent(template).format(
            directives="\n".join(directives),
            envcmds="\n".join(envcmds or []),
            envvars="\n".join([f"export {k}={v}" for k, v in (envvars or {}).items()]),
            execution="\n".join([*initcmds, *execution]),
            manual=manual,
            ECF_NAME="ECF_NAME",
        )
        return re.sub(r"\n\n\n+", "\n\n", rs.strip())

    def _scheduler(self, config: dict, subsection: str) -> JobScheduler:
        """
        Use the execution and platform blocks to build a JobScheduler object.
        """
        execution = config[subsection][STR.execution]
        if not (platform := config.get(STR.platform)):
            msg = f"Required '{STR.platform}' block missing in config."
            raise UWConfigError(msg)
        threads = execution.get(STR.threads)
        rundir = config[subsection][STR.rundir]
        resources = {
            STR.account: platform[STR.account],
            STR.rundir: rundir,
            STR.scheduler: platform[STR.scheduler],
            STR.stdout: "%s.out" % Path(rundir, subsection),
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
