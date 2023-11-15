"""
Support for rendering Jinja2 templates.
"""

import os
from typing import Dict, List, Optional, Set, Union

import yaml
from jinja2 import (
    BaseLoader,
    Environment,
    FileSystemLoader,
    StrictUndefined,
    Template,
    Undefined,
    meta,
)
from jinja2.exceptions import UndefinedError

from uwtools.config.support import format_to_config
from uwtools.logging import MSGWIDTH, log
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import get_file_type, readable, writable

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


def dereference(val: _YAMLVal, context: dict, local: Optional[dict] = None) -> _YAMLVal:
    """
    Render Jinja2 syntax, wherever possible.

    :param val: A value possibly containing Jinja2 syntax.
    :param context: Values to use when rendering Jinja2 syntax.
    :param local: Local sibling values to use if a match is not found in context.
    :return: The input value, with Jinja2 syntax rendered.
    """

    # Build a replacement value with Jinja2 syntax rendered. Depend on recursion for dict and list
    # values; render strings; and return objects of any other type unmodified. Rendering may fail
    # for valid reasons -- notably a replacement value not being available in the given context
    # object. In such cases, return the original value: Any unrendered Jinja2 syntax it contains may
    # may be rendered by later processing with better context.

    # Note that, for rendering performed on dict values, replacement values will be taken from, in
    # priority order, 1. The full context dict, 2. Local sibling values in the dict.

    log.debug("Rendering: %s", val)
    if isinstance(val, dict):
        return {k: dereference(v, context, local=val) for k, v in val.items()}
    if isinstance(val, list):
        return [dereference(v, context) for v in val]
    if isinstance(val, str):
        try:
            rendered = (
                _register_filters(Environment(undefined=StrictUndefined))
                .from_string(val)
                .render({**(local or {}), **context})
            )
            return _reify_scalar_str(rendered)
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.debug("Rendering ERROR: %s", e)
    log.debug("Rendered: %s", val)
    return val


def render(
    input_file: OptionalPath,
    output_file: OptionalPath,
    values_file: DefinitePath,
    values_format: Optional[str] = None,
    overrides: Optional[Dict[str, str]] = None,
    values_needed: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Render a Jinja2 template.

    :param input_file: Path to the Jinja2 template file to render.
    :param output_file: Path to the file to write the rendered Jinja2 template to.
    :param values_file: Path to the file supplying values to render the template.
    :param keq_eq_val_pairs: "key=value" strings to supplement values-file values.
    :param values_needed: Just issue a report about variables needed to render the template?
    :param dry_run: Run in dry-run mode?
    """
    _report(locals())
    values = _set_up_values_obj(
        values_file=values_file, values_format=values_format, overrides=overrides
    )
    with readable(input_file) as f:
        template_str = f.read()
    template = J2Template(values=values, template_str=template_str)
    undeclared_variables = template.undeclared_variables

    # If a report of variables required to render the template was requested, make that report and
    # then return.

    if values_needed:
        log.info("Value(s) needed to render this template are:")
        for var in sorted(undeclared_variables):
            log.info(var)
        return True

    # Check for missing values required to render the template. If found, report them and raise an
    # exception.

    missing = [var for var in undeclared_variables if var not in values.keys()]
    if missing:
        msg = "Required value(s) not provided:"
        log.error(msg)
        for key in missing:
            log.error(key)
        return False

    # In dry-run mode, display the rendered template and then return.

    if dry_run:
        rendered_template = template.render()
        for line in rendered_template.split("\n"):
            log.info(line)
        return True

    # Write rendered template to file.

    with writable(output_file) as f:
        print(template.render(), file=f)
    return True


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


def _report(args: dict) -> None:
    """
    Log the names and values of arguments.

    :param args: The argument names and their values.
    """
    dashes = lambda: log.debug("-" * MSGWIDTH)
    log.debug("Internal arguments:")
    dashes()
    for varname, value in args.items():
        log.debug("%16s: %s", varname, value)
    dashes()


def _set_up_values_obj(
    values_file: OptionalPath = None,
    values_format: Optional[str] = None,
    overrides: Optional[Dict[str, str]] = None,
) -> dict:
    """
    Collect template-rendering values based on an input file, if given, or otherwise on the shell
    environment; and supplemented with override values from given "key=value" strings.

    :param values_file: Path to the file supplying values to render the template.
    :param keq_eq_val_pairs: "key=value" strings to supplement values-file values.
    :returns: The collected values.
    """
    if values_file:
        if values_format is None:
            values_format = get_file_type(values_file)
        values_class = format_to_config(values_format)
        values = values_class(values_file).data
        log.debug("Read initial values from %s", values_file)
    else:
        values = dict(os.environ)  # Do not modify os.environ: Make a copy.
        log.debug("Initial values taken from environment")
    if overrides:
        values.update(overrides)
        log.debug("Updated values with overrides: %s", " ".join(overrides))
    return values
