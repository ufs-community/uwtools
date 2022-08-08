'''
Template classes

'''


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

    def __init__(self, configure_obj, template_path=None, template_str=None):

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

        if template_path is not None:
            self.template = self._load_file(template_path)
        elif template_str is not None:
            self.template = self._load_string(template_str)
        else:
            # Error here. Must provide a template.
            continue

    def dump_file(self,utput_path):

        '''
        Write rendered template to the output_path provided

        Parameters
        ----------
        output_path : Path

        '''
        pass

    def _load_file(self, template_file):
        '''
        Load the Jinja2 template from the file provided.

        Returns
        -------
        Jinja2 Template object
        '''
        pass

    def _load_string(self):
        '''
        Load the Jinja2 template from the string provided.

        Returns
        -------
        Jinja2 Template object
        '''
        pass

    def render_template(self):
        ''' Render the Jinja2 template so that it's available in memory

        Returns
        -------
        A string containing a rendered Jinja2 template.
        '''
        pass

    def undeclared_variables(self):

        ''' Generates a list of variables needed for self.template '''
        pass

    def validate_config(self):

        '''
        Match the provided configure_obj with the undeclared variables.
        Provide user feedback about variables that should be provided
        before exiting.
        '''
        pass



