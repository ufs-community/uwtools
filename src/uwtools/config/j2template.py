"""
Support for handling Jinja2 templates.
"""

import os
from typing import List, Optional, Set, Union

import yaml
from jinja2 import (
    BaseLoader,
    DebugUndefined,
    Environment,
    FileSystemLoader,
    Template,
    Undefined,
    meta,
)
from jinja2.exceptions import UndefinedError

from uwtools.logging import log
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import readable, writable

_YAMLVal = Union[bool, dict, float, int, list, str]


class J2Template:
    """
    Reads Jinja templates from files or strings, and renders them using the user-provided values.
    """

    def __init__(
        self,
        values: dict,
        template_path: OptionalPath = None,
        template_str: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        :param values: Values needed to render the provided template.
        :param template_path: Path to a Jinja2 template file.
        :param template_str: An in-memory Jinja2 template.
        :raises: RuntimeError: If neither a template file or path is provided.
        """
        self._values = values
        self._template_path = template_path
        self._template_str = template_str
        self._loader_args = kwargs.get("loader_args", {})
        if template_path is not None:
            self._template = self._load_file(template_path)
        elif template_str is not None:
            self._template = self._load_string(template_str)
        else:
            raise RuntimeError("Must provide either a template path or a template string")

    # Public methods

    def dump(self, output_path: OptionalPath) -> None:
        """
        Write rendered template to the path provided.

        :param output_path: Path to file to write.
        """
        msg = f"Writing rendered template to output file: {output_path}"
        log.debug(msg)
        with writable(output_path) as f:
            print(self.render(), file=f)

    def render(self) -> str:
        """
        Render the Jinja2 template so that it's available in memory.

        :return: A string containing a rendered Jinja2 template.
        """
        return self._template.render(self._values)

    @property
    def undeclared_variables(self) -> Set[str]:
        """
        Returns the names of variables needed to render the template.

        :return: Names of variables needed to render the template.
        """
        if self._template_str is not None:
            j2_parsed = self._j2env.parse(self._template_str)
        else:
            assert self._template_path is not None
            with readable(self._template_path) as file_:
                j2_parsed = self._j2env.parse(file_.read())
        return meta.find_undeclared_variables(j2_parsed)

    # Private methods

    def _load_file(self, template_path: DefinitePath) -> Template:
        """
        Load the Jinja2 template from the file provided.

        :param template_path: Filesystem path to the Jinja2 template file.
        :return: The Jinja2 template object.
        """
        self._j2env = Environment(loader=FileSystemLoader(searchpath="/"))
        _register_filters(self._j2env)
        return self._j2env.get_template(str(template_path))

    def _load_string(self, template: str) -> Template:
        """
        Load the Jinja2 template from the string provided.

        :param template: An in-memory Jinja2 template.
        :return: The Jinja2 template object.
        """
        self._j2env = Environment(loader=BaseLoader(), **self._loader_args)
        _register_filters(self._j2env)
        return self._j2env.from_string(template)


# Public functions


def dereference(val: _YAMLVal, context: dict) -> _YAMLVal:
    """
    Render Jinja2 syntax, wherever possible.

    :param val: A value possibly containing Jinja2 syntax.
    :param context: Values to use when rendering Jinja2 syntax.
    :return: The input value, with Jinja2 syntax rendered.
    """
    if isinstance(val, dict):
        return {k: dereference(v, context) for k, v in val.items()}
    if isinstance(val, list):
        return [dereference(v, context) for v in val]
    if isinstance(val, str):
        try:
            return _reify_scalar_str(
                yaml.safe_load(
                    _register_filters(Environment(undefined=DebugUndefined))
                    .from_string(f"'{val}'")
                    .render(**context)
                )
            )
        except:  # pylint: disable=bare-except
            pass
    return val


# Private functions


def _register_filters(env: Environment) -> Environment:
    """
    Add filters to a Jinja2 Environment.

    :param env: The Environment to add the filters to.
    :return: The input Environment, with filters added.
    """

    def path_join(path_components: List[str]) -> str:
        if any(isinstance(x, Undefined) for x in path_components):
            raise UndefinedError()
        return os.path.join(*path_components)

    filters = dict(
        path_join=path_join,
    )
    env.filters.update(filters)
    return env


def _reify_scalar_str(s: str) -> Union[bool, float, int, str]:
    """
    Reify a string to a Python object, using YAML. Jinja2 templates will be passed as-is.

    :param s: The string to reify.
    """
    try:
        r = yaml.safe_load(s)
    except yaml.YAMLError:
        return s
    return r
