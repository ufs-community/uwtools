"""
Support for rendering Jinja2 templates.
"""

import os
from typing import Dict, List, Optional, Set, Union

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

from uwtools.config.support import TaggedString, format_to_config
from uwtools.logging import MSGWIDTH, log
from uwtools.types import Path, Optional[Path]
from uwtools.utils.file import get_file_format, readable, writable

_ConfigVal = Union[bool, dict, float, int, list, str, TaggedString]


class J2Template:
    """
    Reads Jinja2 templates from files or strings, and renders them using the user-provided values.
    """

    def __init__(self, values: dict, template_source: Union[str, Path]) -> None:
        """
        :param values: Values needed to render the provided template.
        :param template_source: Jinja2 string or template file path (None => read stdin).
        :raises: RuntimeError: If neither a template file or path is provided.
        """
        self._values = values
        self._template = (
            self._load_string(template_source)
            if isinstance(template_source, str)
            else self._load_file(template_source)
        )
        self._template_source = template_source

    # Public methods

    def dump(self, output_path: Optional[Path]) -> None:
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
        if isinstance(self._template_source, str):
            j2_parsed = self._j2env.parse(self._template_source)
        else:
            with open(self._template_source, "r", encoding="utf-8") as f:
                j2_parsed = self._j2env.parse(f.read())
        return meta.find_undeclared_variables(j2_parsed)

    # Private methods

    def _load_file(self, template_path: Path) -> Template:
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
        self._j2env = Environment(loader=BaseLoader())
        _register_filters(self._j2env)
        return self._j2env.from_string(template)


# Public functions


def dereference(val: _ConfigVal, context: dict, local: Optional[dict] = None) -> _ConfigVal:
    """
    Render Jinja2 syntax, wherever possible.

    Build a replacement value with Jinja2 syntax rendered. Depend on recursion for dict and list
    values; render strings; convert values tagged with explicit types; and return objects of other
    types unmodified. Rendering may fail for valid reasons -- notably a replacement value not being
    available in the given context object. In such cases, return the original value: Any unrendered
    Jinja2 syntax it contains may may be rendered by later processing with better context.

    When rendering dict values, replacement values will be taken from, in priority order
      1. The full context dict
      2. Local sibling values in the dict

    :param val: A value possibly containing Jinja2 syntax.
    :param context: Values to use when rendering Jinja2 syntax.
    :param local: Local sibling values to use if a match is not found in context.
    :return: The input value, with Jinja2 syntax rendered.
    """
    rendered: _ConfigVal = val  # fall-back value
    if isinstance(val, dict):
        return {dereference(k, context): dereference(v, context, local=val) for k, v in val.items()}
    if isinstance(val, list):
        return [dereference(v, context) for v in val]
    if isinstance(val, str):
        _deref_debug("Rendering", val)
        rendered = _deref_render(val, context, local)
    elif isinstance(val, TaggedString):
        _deref_debug("Rendering", val.value)
        val.value = _deref_render(val.value, context, local)
        rendered = _deref_convert(val)
    else:
        _deref_debug("Accepting", val)
    return rendered


def render(
    values: Union[dict, Path],
    values_format: Optional[str] = None,
    input_file: Optional[Path] = None,
    output_file: Optional[Path] = None,
    overrides: Optional[Dict[str, str]] = None,
    values_needed: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Check and render a Jinja2 template.

    :param values: Source of values to render the template.
    :param values_format: Format of values when sourced from file.
    :param input_file: Path to read raw Jinja2 template from (None => read stdin).
    :param output_file: Path to write rendered Jinja2 template to (None => write to stdout).
    :param overrides: Supplemental override values.
    :param values_needed: Just report variables needed to render the template?
    :param dry_run: Run in dry-run mode?
    :return: Jinja2 template was successfully rendered.
    """

    # Render template.

    _report(locals())
    if not isinstance(values, dict):
        values = _set_up_values_obj(
            values_file=values, values_format=values_format, overrides=overrides
        )
    with readable(input_file) as f:
        template_str = f.read()
    template = J2Template(values=values, template_source=template_str)
    undeclared_variables = template.undeclared_variables

    # If a report of variables required to render the template was requested, make that report and
    # then return.

    if values_needed:
        return _values_needed(undeclared_variables)

    # Check for missing values required to render the template. If found, report them and raise an
    # exception.

    missing = [var for var in undeclared_variables if var not in values.keys()]
    if missing:
        return _log_missing_values(missing)

    # In dry-run mode, log the rendered template. Otherwise, write the rendered template.

    return (
        _dry_run_template(template.render())
        if dry_run
        else _write_template(output_file, template.render())
    )


# Private functions


def _deref_convert(val: TaggedString) -> _ConfigVal:
    """
    Convert a string tagged with an explicit type.

    If conversion cannot be performed (e.g. the value was tagged as an int but int() is not a value
    that can be represented as an int, the original value will be returned unchanged.

    :param val: A scalar value tagged with an explicit type.
    :return: The value translated to the specified type.
    """
    converted: _ConfigVal = val  # fall-back value
    _deref_debug("Converting", val.value)
    try:
        converted = val.convert()
        _deref_debug("Converted", converted)
    except Exception as e:  # pylint: disable=broad-exception-caught
        _deref_debug("Conversion failed", str(e))
    return converted


def _deref_debug(action: str, val: _ConfigVal) -> None:
    """
    Log a debug-level message related to dereferencing.

    :param action: The dereferencing activity being performed.
    :param val: The value being dereferenced.
    """
    log.debug("[dereference] %s: %s", action, val)


def _deref_render(val: str, context: dict, local: Optional[dict] = None) -> str:
    """
    Render a Jinja2 variable/expression as part of dereferencing.

    If this function cannot render the value, either because it contains no Jinja2 syntax or because
    insufficient context is currently available, a debug message will be logged and the original
    value will be returned unchanged.

    :param val: The value potentially containing Jinja2 syntax to render.
    :param context: Values to use when rendering Jinja2 syntax.
    :param local: Local sibling values to use if a match is not found in context.
    :return: The rendered value (potentially unchanged).
    """
    try:
        rendered = (
            _register_filters(Environment(undefined=StrictUndefined))
            .from_string(val)
            .render({**(local or {}), **context})
        )
        _deref_debug("Rendered", rendered)
    except Exception as e:  # pylint: disable=broad-exception-caught
        _deref_debug("Rendering failed", str(e))
        rendered = val
    return rendered


def _dry_run_template(rendered_template: str) -> bool:
    """
    Log the rendered template and then return as successful.

    :param rendered_template: A string containing a rendered Jinja2 template.
    :return: The successful logging of the template.
    """

    for line in rendered_template.split("\n"):
        log.info(line)
    return True


def _log_missing_values(missing: List[str]) -> bool:
    """
    Log values missing from template and raise an exception.

    :param missing: A list containing the undeclared variables that do not have a corresponding
        match in values.
    :return: Unable to successfully render template.
    """

    log.error("Required value(s) not provided:")
    for key in missing:
        log.error(key)
    return False


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
    values_file: Optional[Path] = None,
    values_format: Optional[str] = None,
    overrides: Optional[Dict[str, str]] = None,
) -> dict:
    """
    Collect template-rendering values based on an input file, if given, or otherwise on the shell
    environment. Apply override values.

    :param values_file: Path to the file supplying values to render the template.
    :param values_format: Format of values when sourced from file.
    :param overrides: Supplemental override values.
    :returns: The collected values.
    """
    if values_file:
        if values_format is None:
            values_format = get_file_format(values_file)
        values_class = format_to_config(values_format)
        values: dict = values_class(values_file).data
        log.debug("Read initial values from %s", values_file)
    else:
        values = dict(os.environ)  # Do not modify os.environ: Make a copy.
        log.debug("Initial values taken from environment")
    if overrides:
        values.update(overrides)
        log.debug("Updated values with overrides: %s", " ".join(overrides))
    return values


def _values_needed(undeclared_variables: Set[str]) -> bool:
    """
    Log variables needed to render the template.

    :param undeclared_variables: A set containing the variables needed to render the template.
    :return: Successfully logged values needed.
    """

    # If a report of variables required to render the template was requested, make that report and
    # then return.
    log.info("Value(s) needed to render this template are:")
    for var in sorted(undeclared_variables):
        log.info(var)
    return True


def _write_template(output_file: Optional[Path], rendered_template: str) -> bool:
    """
    Write the rendered template.

    :param output_file: Path to the file to write the rendered Jinja2 template to.
    :param rendered_template: A string containing a rendered Jinja2 template.
    :return: The successful writing of the rendered template.
    """
    with writable(output_file) as f:
        print(rendered_template, file=f)
    return True
