from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING
from pathlib import Path
from textwrap import dedent

from ecflow import Defs, Family, Suite, Task

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.tools import walk_key_path
from uwtools.logging import log
from uwtools.scheduler import JobScheduler
from uwtools.strings import STR

if TYPE_CHECKING:
    from ecflow import NodeContainer
    from libpath import Path

class _ecConstant:
    def __init__(self, value):
        self.val = value

    def __getattr__(self, name):
        def method(*args, **kwargs):
            return self.val
        return method

    def __deepcopy__(self, memo):
        return self

class _ecFlowDef:
    """
    Generate an ecFlow definition file from a YAML config.
    """

    def __init__(self, config: dict | YAMLConfig | Path | None = None) -> None:
        cfgobj = config if isinstance(config, YAMLConfig) else YAMLConfig(config)
        cfgobj = cfgobj.dereference(context={
            "cycle": _ecConstant("%CYCLE%"),
            "timevars": {"fff": "%FHR%"},
            })
        self.refs = {}
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
        Add suites, families, and tasks to the suite definition.

        :param d: The root of the definition tree.
        :param config: Configuration data for these components.
        """
        for key, subconfig in config.items():
            tag, name = self._tag_name(key)
            # Options: extern, vars, suite_*, suites_*
            match tag:
                case "extern":
                    self._add_extern(d, subconfig, name)
                case "vars":
                    self._add_vars(d, subconfig, name)
                case "suite":
                    self._add_suite(d, subconfig, name)
                case "suites":
                    self._add_repeater("suite", d, subconfig, name)

    def _add_extern(
        self,
        parent: NodeContainer,
        config: dict,
        name: str,
    ) -> None:
        pass

    def _add_family(
        self,
        parent: NodeContainer,
        config: dict,
        name: str,
    ) -> None:
        """
        Add a family to a suite.

        :param parent: The parent object to add this suite to.
        :param config: Configuration data for these components.
        :param name: Name of this suite.
        """
        fam = Family(name)
        parent.add_family(fam)
        for key, subconfig in config.items():
            tag, name = self._tag_name(key)
            match tag:
                case "family":
                    self._add_family(fam, subconfig, name)
                case "families":
                    self._add_repeater("family", fam, subconfig, name)
                case "task":
                    self._add_task(fam, subconfig, name)
                case "tasks":
                    self._add_repeater("task", fam, subconfig, name)

    def _add_vars(
        self,
        parent: NodeContainer,
        config: dict,
        name: str,
    ) -> None:
        pass

    def _add_suite(
        self,
        parent: NodeContainer,
        config: dict,
        name: str,
    ) -> None:
        """
        Add a suite to the suite definition.

        :param parent: The parent object to add this suite to.
        :param config: Configuration data for these components.
        :param name: Name of this suite.
        """
        suite = Suite(name)
        parent.add_suite(suite)
        for key, subconfig in config.items():
            tag, name = self._tag_name(key)
            match tag:
                case "vars":
                    self._add_vars(suite, subconfig, name)
                case "family":
                    self._add_family(suite, subconfig, name)
                case "families":
                    self._add_repeater("family", suite, subconfig, name)
                case "task":
                    self._add_task(suite, subconfig, name)
                case "tasks":
                    self._add_repeater("task", suite, subconfig, name)

    def _add_repeater(
        self,
        nodetype: str,
        parent: NodeContainer,
        config: dict,
        name: str,
    ) -> None:
        """
        Add a set of suites to the suite definition.

        :param parent: The parent object to add this suite to.
        :param config: Configuration data for these components.
        :param name: Name of this suite.
        """
        repeat = config["repeat"]
        primary_variable = list(repeat.keys())[0]
        # Check to make sure all lists are the same length.
        try:
            for _i in zip(*repeat.values(), strict=True):
                pass
        except ValueError:
            log.error("All repeat variables under %s must be the same length" % (parent.name()))
            raise

        # Build up the new blocks in the suite definition
        for i in range(len(repeat[primary_variable])):
            # This is not going to work. Need to pass refs down for each repeated item to get the
            # right value.
            self.refs.update({k: v[i] for k, v in repeat.items()})
            new_block = YAMLConfig({name: config}).dereference(context={"ec": self.refs})
            new_name = list(new_block.keys())[0]
            args = {
                "parent": parent,
                "config": new_block[new_name],
                "name": new_name,
            }
            match nodetype:
                case "suite":
                    self._add_suite(**args)
                case "family":
                    self._add_family(**args)
                case "task":
                    self._add_task(**args)

    def _add_task(
        self,
        parent: NodeContainer,
        config: dict,
        name: str,
    ) -> None:
        """
        Add a task to a family.

        :param parent: The parent object to add this task to.
        :param config: Configuration data for these components.
        :param name: Name of this task.
        """
        task = Task(name)
        parent.add_task(task)
        for key, subconfig in config.items():
            tag, name = self._tag_name(key)
            match tag:
                case "event":
                    pass
                case "meter":
                    pass
                case "label":
                    pass
                case "limit":
                    pass
                case "vars":
                    task.add_variable(subconfig)
                case "key-path":
                    self._create_ecf_script(task, subconfig)

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
        path = Path(".", Path(task.get_abs_node_path()).parent, f"{task.name().split('_')[-1]}.ecf").resolve()
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
