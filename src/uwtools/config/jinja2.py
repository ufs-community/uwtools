"""
Support for rendering Jinja2 templates.
"""

import os
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Optional, Union

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, Undefined, meta
from jinja2.exceptions import UndefinedError

from uwtools.config.support import UWYAMLConvert, UWYAMLRemove, format_to_config
from uwtools.exceptions import UWConfigRealizeError
from uwtools.logging import INDENT, MSGWIDTH, log
from uwtools.utils.file import get_file_format, readable, writable

_ConfigVal = Union[bool, datetime, dict, float, int, list, str, UWYAMLConvert, UWYAMLRemove]


class J2Template:
    """
    Read Jinja2 templates from files or strings, and render them using the user-provided values.
    """

    def __init__(
        self,
        values: dict,
        template_source: Optional[Union[str, Path]] = None,
        searchpath: Optional[list[str]] = None,
    ) -> None:
        """
        :param values: Values needed to render the provided template.
        :param template_source: Jinja2 string or template file path (None => read stdin).
        :param searchpath: Colon-separated paths to search for extra templates.
        :raises: RuntimeError: If neither a template file or path is provided.
        """
        self._values = values
        self._template_source = template_source
        self._j2env = Environment(
            loader=FileSystemLoader(
                searchpath=(
                    searchpath
                    if searchpath
                    else (
                        self._template_source.parent
                        if isinstance(self._template_source, Path)
                        else []
                    )
                )
            ),
            undefined=StrictUndefined,
        )
        _register_filters(self._j2env)
        self._template = self._j2env.from_string(self._template_str)

    def __repr__(self):
        return self._template_str

    @cached_property
    def _template_str(self):
        """
        A string containing the template.
        """
        if isinstance(self._template_source, str):
            return self._template_source
        with readable(self._template_source) as f:
            return f.read()

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
    def undeclared_variables(self) -> set[str]:
        """
        The names of variables needed to render the template.
        """
        j2_parsed = self._j2env.parse(self._template_str)
        return meta.find_undeclared_variables(j2_parsed)


# Public functions


def dereference(
    val: _ConfigVal, context: dict, local: Optional[dict] = None, keys: Optional[list[str]] = None
) -> _ConfigVal:
    """
    Render Jinja2 syntax, wherever possible.

    Build a replacement value with Jinja2 syntax rendered. Depend on recursion for dict and list
    values; render strings; convert values tagged with explicit types; and return objects of other
    types unmodified. Rendering may fail for valid reasons -- notably a replacement value not being
    available in the given context object. In such cases, return the original value: Any unrendered
    Jinja2 syntax it contains may be rendered by later processing with better context.

    When rendering dict values, replacement values will be taken from, in priority order
      1. The full context dict
      2. Local sibling values in the dict

    :param val: A value possibly containing Jinja2 syntax.
    :param context: Values to use when rendering Jinja2 syntax.
    :param local: Local sibling values to use if a match is not found in context.
    :param keys: The dict keys leading to this value.
    :return: The input value, with Jinja2 syntax rendered.
    """
    rendered: _ConfigVal
    if isinstance(val, dict):
        keys = keys or []
        rendered = {}
        for k, v in val.items():
            if isinstance(v, UWYAMLRemove):
                _deref_debug("Removing value at", ".".join([*keys, k]))
            else:
                kd, vd = [dereference(x, context, val, [*keys, k]) for x in (k, v)]
                rendered[kd] = vd
    elif isinstance(val, list):
        rendered = [dereference(v, context) for v in val]
    elif isinstance(val, str):
        _deref_debug("Rendering", val)
        rendered = _deref_render(val, context, local)
    elif isinstance(val, UWYAMLConvert):
        _deref_debug("Rendering", val.value)
        val.value = _deref_render(val.value, context, local)
        rendered = _deref_convert(val)
    else:
        _deref_debug("Accepting", val)
        rendered = val
    return rendered


def render(
    values_src: Optional[Union[dict, Path]] = None,
    values_format: Optional[str] = None,
    input_file: Optional[Path] = None,
    output_file: Optional[Path] = None,
    overrides: Optional[dict[str, str]] = None,
    env: bool = False,
    searchpath: Optional[list[str]] = None,
    values_needed: bool = False,
    dry_run: bool = False,
) -> Optional[str]:
    """
    Check and render a Jinja2 template.

    :param values_src: Source of values to render the template.
    :param values_format: Format of values when sourced from file.
    :param input_file: Path to read raw Jinja2 template from (None => read stdin).
    :param output_file: Path to write rendered Jinja2 template to (None => write to stdout).
    :param overrides: Supplemental override values.
    :param env: Supplement values with environment variables?
    :param searchpath: Paths to search for extra templates.
    :param values_needed: Just report variables needed to render the template?
    :param dry_run: Run in dry-run mode?
    :return: The unrendered template if values_needed is True, the rendered template, or None.
    """
    _report(locals())
    values = _supplement_values(
        values_src=values_src, values_format=values_format, overrides=overrides, env=env
    )
    template = J2Template(values=values, template_source=input_file, searchpath=searchpath)
    undeclared_variables = template.undeclared_variables

    # If a report of variables required to render the template was requested, make that report and
    # then return the unrendered template.

    if values_needed:
        _values_needed(undeclared_variables)
        return str(template)

    # Render the template. If there are missing values, report them and return an error to the
    # caller.

    missing = [var for var in undeclared_variables if var not in values.keys()]
    if missing:
        _log_missing_values(missing)
        return None
    try:
        rendered = template.render()
    except UndefinedError as e:
        log.error("Template render failed with error: %s", str(e))
        return None

    # Log (dry-run mode) or write the rendered template.

    return _dry_run_template(rendered) if dry_run else _write_template(output_file, rendered)


def unrendered(s: str) -> bool:
    """
    Does the supplied string contain unrendered Jinja2 variables/expressions?

    :param s: The string to check for unrendered content.
    :return: ``True`` if unrendered content was found, ``False`` otherwise.
    """
    try:
        Environment(undefined=StrictUndefined).from_string(s).render({})
        return False
    except UndefinedError:
        return True


# Private functions


def _deref_convert(val: UWYAMLConvert) -> _ConfigVal:
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

    If the value cannot be rendered, perhaps due to missing values or syntax errors, a debug message
    will be logged and the original value will be returned unchanged.

    :param val: The value potentially containing Jinja2 syntax to render.
    :param context: Values to use when rendering Jinja2 syntax.
    :param local: Local sibling values to use if a match is not found in context.
    :return: The rendered value (potentially unchanged).
    """
    env = Environment(undefined=StrictUndefined)
    context = {**(local or {}), **context}
    try:
        rendered = _register_filters(env).from_string(val).render(context)
        if isinstance(yaml.safe_load(rendered), UWYAMLConvert):
            raise UWConfigRealizeError(f"Rendering delayed: {rendered}")
        _deref_debug("Rendered", rendered)
    except Exception as e:  # pylint: disable=broad-exception-caught
        rendered = val
        _deref_debug("Rendering failed", str(e))
    return rendered


def _dry_run_template(rendered_template: str) -> str:
    """
    Log the rendered template and then return as successful.

    :param rendered_template: A string containing a rendered Jinja2 template.
    :return: The passed-in rendered-template string.
    """
    for line in rendered_template.split("\n"):
        log.info(line)
    return rendered_template


def _log_missing_values(missing: list[str]) -> None:
    """
    Log values missing from template and raise an exception.

    :param missing: Variables with no corresponding values.
    """
    log.error("Value(s) required to render template not provided:")
    for key in missing:
        log.error(f"{INDENT}{key}")


def _register_filters(env: Environment) -> Environment:
    """
    Add filters to a Jinja2 Environment.

    :param env: The Environment to add the filters to.
    :return: The input Environment, with filters added.
    """

    def path_join(path_components: list[str]) -> str:
        if any(isinstance(x, Undefined) for x in path_components):
            raise UndefinedError()
        return os.path.join(*path_components)

    filters = dict(env=lambda var: os.environ[var], path_join=path_join)
    env.filters.update(filters)
    return env


def _report(args: dict) -> None:
    """
    Log the names and values of arguments.

    :param args: The argument names and their values.
    """
    dashes = lambda: log.debug("-" * MSGWIDTH)
    log.debug("Internal arguments when rendering template:")
    dashes()
    for varname, value in args.items():
        log.debug("%16s: %s", varname, value)
    dashes()


def _supplement_values(
    values_src: Optional[Union[dict, Path]] = None,
    values_format: Optional[str] = None,
    overrides: Optional[dict[str, str]] = None,
    env: bool = False,
) -> dict:
    """
    Optionally supplement values from given source with overrides and/or environment variables.

    :param values_src: Source of values to render the template.
    :param values_format: Format of values when sourced from file.
    :param overrides: Override values.
    :param env: Supplement values with environment variables?
    :returns: The final set of template-rendering values.
    """
    values: dict
    if isinstance(values_src, Path):
        values_format = values_format or get_file_format(values_src)
        values_src_class = format_to_config(values_format)
        values = values_src_class(values_src).data
        log.debug("Read initial template values from %s", values_src)
    else:
        values = values_src or {}
    if overrides:
        values.update(overrides)
        log.debug("Supplemented template values with overrides: %s", " ".join(overrides))
    if env:
        values.update(os.environ)
        log.debug("Supplemented template values with environment variables")
    return values


def _values_needed(undeclared_variables: set[str]) -> None:
    """
    Log variables needed to render the template.

    :param undeclared_variables: A set containing the variables needed to render the template.
    """
    log.info("Value(s) needed to render this template are:")
    for var in sorted(undeclared_variables):
        log.info(f"{INDENT}{var}")


def _write_template(output_file: Optional[Path], rendered_template: str) -> str:
    """
    Write the rendered template.

    :param output_file: Path to the file to write the rendered Jinja2 template to.
    :param rendered_template: A string containing a rendered Jinja2 template.
    :return: The passed-in rendered-template string.
    """
    with writable(output_file) as f:
        print(rendered_template, file=f)
    return rendered_template
