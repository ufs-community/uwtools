"""
Canonical strings used throughout uwtools.
"""

from dataclasses import dataclass, fields
from typing import Dict, List


@dataclass(frozen=True)
class FORMAT:
    """
    A mapping from config format names to literal strings.
    """

    # Canonical strings:

    _atparse: str = "atparse"
    _fieldtable: str = "fieldtable"
    _ini: str = "ini"
    _jinja2: str = "jinja2"
    _nml: str = "nml"
    _sh: str = "sh"
    _xml: str = "xml"
    _yaml: str = "yaml"

    # Variants:

    atparse: str = _atparse
    bash: str = _sh
    cfg: str = _ini
    fieldtable: str = _fieldtable
    ini: str = _ini
    jinja2: str = _jinja2
    nml: str = _nml
    sh: str = _sh
    yaml: str = _yaml
    yml: str = _yaml

    @staticmethod
    def extensions() -> List[str]:
        """
        Returns recognized filename extensions.
        """
        return [FORMAT.ini, FORMAT.nml, FORMAT.sh, FORMAT.yaml]

    @staticmethod
    def formats() -> Dict[str, str]:
        """
        Returns the recognized format names.
        """
        return {
            field.name: str(getattr(FORMAT, field.name))
            for field in fields(FORMAT)
            if not field.name.startswith("_")
        }


@dataclass(frozen=True)
class STR:
    """
    A lookup map for CLI-related strings.
    """

    action: str = "action"
    batch: str = "batch"
    cfgfile: str = "config_file"
    chgrescube: str = "chgres_cube"
    compare: str = "compare"
    config: str = "config"
    cycle: str = "cycle"
    dryrun: str = "dry_run"
    env: str = "env"
    file1fmt: str = "file_1_format"
    file1path: str = "file_1_path"
    file2fmt: str = "file_2_format"
    file2path: str = "file_2_path"
    fv3: str = "fv3"
    graphfile: str = "graph_file"
    help: str = "help"
    infile: str = "input_file"
    infmt: str = "input_format"
    keyvalpairs: str = "key_eq_val_pairs"
    mode: str = "mode"
    model: str = "model"
    outfile: str = "output_file"
    outfmt: str = "output_format"
    partial: str = "partial"
    quiet: str = "quiet"
    realize: str = "realize"
    render: str = "render"
    rocoto: str = "rocoto"
    run: str = "run"
    schemafile: str = "schema_file"
    searchpath: str = "search_path"
    sfcclimogen: str = "sfc_climo_gen"
    suppfiles: str = "supplemental_files"
    task: str = "task"
    tasks: str = "tasks"
    template: str = "template"
    total: str = "total"
    translate: str = "translate"
    validate: str = "validate"
    valsfile: str = "values_file"
    valsfmt: str = "values_format"
    valsneeded: str = "values_needed"
    verbose: str = "verbose"
