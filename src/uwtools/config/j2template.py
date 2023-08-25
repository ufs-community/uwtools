"""
Support for handling Jinja2 templates.
"""

import logging
import os
from typing import List, Optional, Set

from jinja2 import BaseLoader, Environment, FileSystemLoader, Template, meta


class J2Template:
    """
    Reads Jinja templates from files or strings, and renders them using the user-provided
    configuration object.
    """

    def __init__(
        self,
        configure_obj: dict,
        template_path: Optional[str] = None,
        template_str: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        :param configure_obj: Key/value pairs needed to render the provided template.
        :param template_path: Path to a Jinja2 template file.
        :param template_str: An in-memory Jinja2 template.
        :raises: RuntimeError: If neither a template file or path is provided.
        """
        self._configure_obj = configure_obj
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

    def dump_file(self, output_path: str) -> None:
        """
        Write rendered template to the path provided.

        :param output_path: Path to file to write.
        """
        msg = f"Writing rendered template to output file: {output_path}"
        logging.debug(msg)
        with open(output_path, "w+", encoding="utf-8") as f:
            print(self.render(), file=f)

    def render(self) -> str:
        """
        Render the Jinja2 template so that it's available in memory.

        :return: A string containing a rendered Jinja2 template.
        """
        return self._template.render(self._configure_obj)

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
            with open(self._template_path, encoding="utf-8") as file_:
                j2_parsed = self._j2env.parse(file_.read())
        return meta.find_undeclared_variables(j2_parsed)

    # Private methods

    def _load_file(self, template_path: str) -> Template:
        """
        Load the Jinja2 template from the file provided.

        :param template_path: Filesystem path to the Jinja2 template file.
        :return: The Jinja2 template object.
        """
        self._j2env = Environment(loader=FileSystemLoader(searchpath="/"))
        _register_filters(self._j2env)
        return self._j2env.get_template(template_path)

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


def path_join(path_components: List[str]) -> str:
    """
    A Jinja2 filter definition for joining paths.

    :param path_components: The filesystem path components to join into a single path.
    :return: The joined path.
    """
    return os.path.join(*path_components)


# Private functions


def _register_filters(j2env: Environment) -> None:
    """
    Register a set of filters with a Jinja2 Environment.

    :param j2env: The Jinja2 Environment with which to register filters.
    """
    j2env.filters["path_join"] = path_join
