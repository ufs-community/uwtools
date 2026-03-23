from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ecflow import Defs, Family, Suite, Task

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.logging import log

if TYPE_CHECKING:
    from ecflow import NodeContainer
    from libpath import Path


@dataclass(frozen=True)
class STR:
    """
    A lookup map for ecFlow-related strings.
    """

    workflow: str = "workflow"


class _ecFlowDef:
    """
    Generate an ecFlow definition file from a YAML config.
    """

    def __init__(self, config: dict | YAMLConfig | Path | None = None) -> None:
        cfgobj = config if isinstance(config, YAMLConfig) else YAMLConfig(config)
        cfgobj.dereference()
        self.refs = {}
        self._config = cfgobj.data
        self._add_workflow(self._config)

    def __str__(self):
        return self.d.__str__()

    def _add_workflow(self, config: dict) -> None:
        """
        Create the root Def object.

        :param config: Configuration data for this object.
        """
        config, self.d = config[STR.workflow], Defs()
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
