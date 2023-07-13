"""
Template classes.
"""

import logging
import os
from typing import Optional

from jinja2 import BaseLoader, Environment, FileSystemLoader, meta

from uwtools import logger


def register_filters(j2env):
    """
    Given a Jinja2 environment, register a set of filters recognized by the UW Tools parser.
    """

    j2env.filters["path_join"] = path_join


def path_join(arg):
    """
    A Jinja2 filter definition for joining paths.
    """
    return os.path.join(*arg)


class J2Template:
    """
    This class reads in Jinja templates from files or strings, and renders the template given the
    user-provided configuration object.

    Attributes
    ----------

    configure_obj : dict
        The key/value pairs needed to fill in the provided template.
        Defaults to the user's shell environment.

    template
        Jinja2 template object

    undeclared_variables : list
        List of variables needed given a Jinja2 template

    Methods
    -------

    _load_file()
        Wrapper around loading a Jinja2 template from a file.

    _load_string()
        Wrapper around loading a Jinja2 template from a string

    dump_file(output_path)
        Wrapper around writing the template to an output path

    validate_config()
        Checks to ensure that the provided configure_obj is sufficient
        to meet the needs of the undeclared_variables in the template
    """

    def __init__(
        self,
        configure_obj: dict,
        template_path: Optional[str] = None,
        template_str: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Parameters
        ----------
        configure_obj
            See class-level docstring
        template_path
            Path to a Jinja2 template file
        template_str
            A Jinja2 template

        Keyword Arguments
        -----------------
        loader_args : dict
            A dictionary of arguments to pass to the J2 loader
        log_name : str
            The name of the logging object to be used.
        """

        self.log = logging.getLogger(kwargs.get("log_name"))

        self.configure_obj = configure_obj
        self.template_path = template_path
        self.template_str = template_str
        self.loader_args = kwargs.get("loader_args", {})

        if template_path is not None:
            self.template = self._load_file(template_path)
        elif template_str is not None:
            self.template = self._load_string(template_str)
        else:
            raise RuntimeError("Must provide either a template path or a template string")

    def dump_file(self, output_path: str) -> None:
        """
        Write rendered template to the path provided.

        Parameters
        ----------
        output_path
            Path to file to write
        """
        msg = f"Writing rendered template to output file: {output_path}"
        self.log.debug(msg)
        with open(output_path, "w+", encoding="utf-8") as file_:
            print(self.render_template(), file=file_)

    @logger.verbose()
    def _load_file(self, template_path):
        """
        Load the Jinja2 template from the file provided.

        Returns
        -------
        Jinja2 Template object
        """

        self._j2env = Environment(loader=FileSystemLoader(searchpath="/"))
        register_filters(self._j2env)
        return self._j2env.get_template(template_path)

    @logger.verbose()
    def _load_string(self, template_str):
        """
        Load the Jinja2 template from the string provided.

        Returns
        -------
        Jinja2 Template object
        """

        self._j2env = Environment(loader=BaseLoader(), **self.loader_args)
        register_filters(self._j2env)
        return self._j2env.from_string(template_str)

    def render_template(self):
        """
        Render the Jinja2 template so that it's available in memory.

        Returns
        -------
        A string containing a rendered Jinja2 template.
        """
        return self.template.render(self.configure_obj)

    @property
    def undeclared_variables(self):
        """
        Generates a list of variables needed for self.template.
        """
        if self.template_str is not None:
            j2_parsed = self._j2env.parse(self.template_str)
        else:
            assert self.template_path is not None
            with open(self.template_path, encoding="utf-8") as file_:
                j2_parsed = self._j2env.parse(file_.read())
        return meta.find_undeclared_variables(j2_parsed)
