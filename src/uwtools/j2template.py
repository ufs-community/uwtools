'''
Template classes

'''

import os

from jinja2 import Environment, BaseLoader, FileSystemLoader, meta

def register_filters(j2env):

    ''' Given a Jinja2 environment, register a set of filters recognized
    by the UW Tools parser. '''

    j2env.filters["path_join"] = path_join


def path_join(arg):

    ''' A Jinj2 filter definition for joining paths '''
    return os.path.join(*arg)

class J2Template():

    '''
    This class reads in Jinja templates from files or strings, and
    renders the template given the user-provided configuration object.

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

    '''

    def __init__(self, configure_obj, template_path=None,
                 template_str=None, loader_args=None):

        '''
        Parameters
        ----------
        configure_obj : dict (See above)
        template_path : Path
            Path to a Jinja2 template file
        template_str : str
            A Jinja2 template string

        '''
        self.configure_obj = configure_obj
        self.template_path = template_path
        self.template_str = template_str
        self.loader_args = loader_args if loader_args is not None else {}
        if template_path is not None:
            self.template = self._load_file(template_path)
        elif template_str is not None:
            self.template = self._load_string(template_str)
        else:
            # Error here. Must provide a template
            pass


    def dump_file(self,output_path):

        '''
        Write rendered template to the output_path provided

        Parameters
        ----------
        output_path : Path

        '''
        with open(output_path,'w+',encoding='utf-8') as file_:
            file_.write(self.render_template() + "\n")


    def _load_file(self, template_path):
        '''
        Load the Jinja2 template from the file provided.

        Returns
        -------
        Jinja2 Template object
        '''

        self._j2env=Environment(loader=FileSystemLoader(searchpath=['','/']),
                               trim_blocks=True,lstrip_blocks=True)
        register_filters(self._j2env)
        return self._j2env.get_template(template_path.replace('\\','/'))

    def _load_string(self,template_str):
        '''
        Load the Jinja2 template from the string provided.

        Returns
        -------
        Jinja2 Template object
        '''

        self._j2env=Environment(loader=BaseLoader(), **self.loader_args)
        register_filters(self._j2env)
        return self._j2env.from_string(template_str)

    def render_template(self):
        ''' Render the Jinja2 template so that it's available in memory

        Returns
        -------
        A string containing a rendered Jinja2 template.
        '''
        return self.template.render(self.configure_obj)

    @property
    def undeclared_variables(self):

        ''' Generates a list of variables needed for self.template '''
        if self.template_str is not None:
            j2_parsed = self._j2env.parse(self.template_str)
        else:
            with open(self.template_path,encoding='utf-8') as file_:
                j2_parsed = self._j2env.parse(file_.read())
        return meta.find_undeclared_variables(j2_parsed)
