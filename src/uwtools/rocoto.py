"""
Support for writing a Rocoto XML using J2Templating
"""

from uwtools.j2template import J2Template
from uwtools.config import YAMLConfig

# private functions
def _add_jobname(tasks: dict) -> None:
    """
    Add the jobname entry for all the tasks in the workflow.

    :param tasks: Dict of tasks in workflow.
    """
    if not isinstance(tasks, dict):
        return
    for task, task_settings in tasks.items():
        task_type = task.split("_", maxsplit=1)[0]
        if task_type == "task":
            # Use the provided attribute if it is present, otherwise use
            # the name in the key
            tasks[task]["jobname"] = \
                task_settings.get("attrs", {}).get("name") or \
                task.split("_", maxsplit=1)[1]
        elif task_type == "metatask":
            _add_jobname(task_settings)

# Main function
def write_rocoto_xml(input_yaml: str, input_template: str, rendered_output: str) -> None:
    """
    Main entry point.

    :param input_yaml: Yaml file provided by the user.
    :param input_template: Path to input template file.
    :param rendered_output: Path to directory to write rendered XML file.
    """
    # make an instance of the YAMLConfig class
    # pass the input yaml to return a dict
    config_obj = YAMLConfig(input_yaml)["rocoto"]
    _add_jobname(config_obj)
   
    # render the template
    template = J2Template(configure_obj=config_obj, template_path=input_template)
    template.dump_file(output_path=rendered_output) 
