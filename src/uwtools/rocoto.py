"""
Support for creating Rocoto XML workflow documents.
"""

from uwtools.config.core import YAMLConfig
from uwtools.config.j2template import J2Template

# Private functions


def _add_jobname(tree: dict) -> None:
    """
    Add a "jobname" attribute to each "task" element in the given config tree.

    :param tree: A config tree containing "task" elements..
    """
    for element, subtree in tree.items():
        element_parts = element.split("_", maxsplit=1)
        element_type = element_parts[0]
        if element_type == "task":
            # Use the provided attribute if it is present, otherwise use the name in the key.
            task_name = element_parts[1]
            tree[element]["jobname"] = subtree.get("attrs", {}).get("name") or task_name
        elif element_type == "metatask":
            _add_jobname(subtree)


# Public functions
def write_rocoto_xml(input_yaml: str, input_template: str, rendered_output: str) -> None:
    """
    Main entry point.

    :param input_yaml: Path to YAML input file.
    :param input_template: Path to input template file.
    :param rendered_output: Path to write rendered XML file.
    """
    values = YAMLConfig(input_yaml)
    tasks = values["tasks"]
    if isinstance(tasks, dict):
        _add_jobname(tasks)

    # Render the template.
    template = J2Template(values=values.data, template_path=input_template)
    template.dump_file(output_path=rendered_output)
