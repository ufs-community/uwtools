import xml.etree.ElementTree as ET
from importlib import resources
from pathlib import Path
from typing import Any, Dict


class RocotoXML:
    """
    A base class specifying methods to manipulate and generate XML files.
    """

    # Helper functions

    def doctype(self, entities: Dict[str, Any]) -> str:
        """
        Generate the DOCTYPE section.
        """
        pass

    def entity(self, name: str) -> str:
        """
        Return a reference to the given ENTITY name.
        """
        pass

    def fixup(self, xml: str, entities: Dict[str, str]) -> str:
        """
        Correct unwanted &-escaping.
        """
        pass

    # Main Methods

    def __init__(self):
        """
        Construct XML document into a tree structure.
        """
        with resources.as_file(resources.files("uwtools.resources")) as path:
            with open(path / "rocoto.xml", "r", encoding="utf-8") as f:
                self._tree = ET.parse(f)

    def write(self, output_dir: str) -> None:
        """
        Write rendered template to the directory provided.

        :param output_path: Path to directory to write.
        """
        # pylint: disable=line-too-long
        self._tree.write(
            Path(output_dir) / "contents.xml", encoding="utf-8", xml_declaration=True, method="xml"
        )
