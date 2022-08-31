
#pylint: disable=invalid-name
'''
J2Template Class
'''

from jinja2 import Environment, BaseLoader, FileSystemLoader, meta
from uwtools.config import YAMLConfig

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

    def __init__(self, configure_path=None, data=None, template_path=None, template_str=None):
        '''
        Parameters
        ----------
        configure_obj : dict (See above)
        template_path : Path
            Path to a Jinja2 template file
        template_str : str
            A Jinja2 template string
        '''
        if configure_path is not None:
            self.configure_obj = YAMLConfig(configure_path)
        elif data is not None:
            self.configure_obj = data
        if template_path is not None:
            self.template_path = template_path
            self.template = self.__load_file(template_path)
        elif template_str is not None:
            self.template = self.__load_string(template_str)
        else:
            print('usr logger for error statment')

    def __load_file(self,template_path):
        '''Loads the Jinja2 template template from file and returns obj'''
        self.__j2env=Environment(loader=FileSystemLoader(searchpath='/'),
                               trim_blocks=True,lstrip_blocks=True)
        return self.__j2env.get_template(template_path)

    def __load_string(self,template_str):
        '''Loads the Jinja2 template object from a string'''
        return Environment(loader=BaseLoader()).from_string(template_str)

    def render_template(self):
        ''' Render the Jinja2 template so that it's available in memory'''
        return self.template.render(self.configure_obj)

    def undeclared_variables(self):
        ''' Generates a list of variables needed for self.template '''
        with open(self.template_path ,encoding='utf-8') as __file:
            j2_parsed = self.__j2env.parse(__file.read())
            return meta.find_undeclared_variables(j2_parsed)

    def dump_file(self,output_path):
        '''
        Write rendered template to the output_path provided
        '''
        __render = self.render_template()
        with open(output_path,'w+',encoding='utf-8') as __file:
            __file.write(__render)

    def validate_config(self):
        '''
        Match the provided configure_obj with the undeclared variables.
        Provide user feedback about variables that should be provided
        before exiting.
        '''

        values_needed = self.undeclared_variables()

        for key,value in self.configure_obj.items():
            if key in values_needed:
                print(f"SET     {key} : {value}")
            else:
                print(f"Value   {key} : {value} not in template")

        for value in values_needed:
            if value not in self.configure_obj:
                print(f"SET NOT {value}")
