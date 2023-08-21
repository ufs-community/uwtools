"""
Support for creating Rocoto XML workflow documents.
"""

from uwtools.config import YAMLConfig
from uwtools.j2template import J2Template


# Private functions
def _add_jobname(tasks: dict) -> None:
    """
    Add the jobname entry for all the tasks in the workflow.

    :param tasks: Dict of tasks in workflow.
    """
    for task, task_settings in tasks.items():
        task_split = task.split("_", maxsplit=1)
        task_type = task_split[0]
        if task_type == "task":
            # Use the provided attribute if it is present, otherwise use the name in the key.
            tasks[task]["jobname"] = task_settings.get("attrs", {}).get("name") or task_split[1]
        elif task_type == "metatask":
            _add_jobname(task_settings)


# Public functions
def write_rocoto_xml(input_yaml: str, input_template: str, rendered_output: str) -> None:
    """
    Main entry point.

    :param input_yaml: Path to YAML input file.
    :param input_template: Path to input template file.
    :param rendered_output: Path to directory to write rendered XML file.
    """
    # Make an instance of the YAMLConfig class.
    # Pass the input yaml to return a dict.
    config_obj = YAMLConfig(input_yaml)["rocoto"]
    _add_jobname(config_obj.get("tasks"))

    # Render the template.
    template = J2Template(configure_obj=config_obj, template_path=input_template)
    template.dump_file(output_path=rendered_output)
