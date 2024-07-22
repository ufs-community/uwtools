"""
Canonical strings used throughout uwtools.
"""

from dataclasses import dataclass, fields


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
    def extensions() -> list[str]:
        """
        Returns recognized filename extensions.
        """
        return [FORMAT.ini, FORMAT.nml, FORMAT.sh, FORMAT.yaml]

    @staticmethod
    def formats() -> dict[str, str]:
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
    String lookup map.
    """

    action: str = "action"
    batch: str = "batch"
    cfgfile: str = "config_file"
    chgrescube: str = "chgres_cube"
    classname: str = "classname"
    compare: str = "compare"
    config: str = "config"
    copy: str = "copy"
    cycle: str = "cycle"
    dryrun: str = "dry_run"
    env: str = "env"
    esggrid: str = "esg_grid"
    execute: str = "execute"
    file1fmt: str = "file_1_format"
    file1path: str = "file_1_path"
    file2fmt: str = "file_2_format"
    file2path: str = "file_2_path"
    file: str = "file"
    filtertopo: str = "filter_topo"
    fv3: str = "fv3"
    globalequivresol: str = "global_equiv_resol"
    graphfile: str = "graph_file"
    help: str = "help"
    infile: str = "input_file"
    infmt: str = "input_format"
    ioda: str = "ioda"
    jedi: str = "jedi"
    keypath: str = "key_path"
    keys: str = "keys"
    keyvalpairs: str = "key_eq_val_pairs"
    leadtime: str = "leadtime"
    link: str = "link"
    makehgrid: str = "make_hgrid"
    makesolomosaic: str = "make_solo_mosaic"
    mode: str = "mode"
    model: str = "model"
    module: str = "module"
    mpas: str = "mpas"
    mpasinit: str = "mpas_init"
    oroggsl: str = "orog_gsl"
    outfile: str = "output_file"
    outfmt: str = "output_format"
    quiet: str = "quiet"
    realize: str = "realize"
    render: str = "render"
    rocoto: str = "rocoto"
    run: str = "run"
    schemafile: str = "schema_file"
    schism: str = "schism"
    searchpath: str = "search_path"
    sfcclimogen: str = "sfc_climo_gen"
    shave: str = "shave"
    targetdir: str = "target_dir"
    task: str = "task"
    tasks: str = "tasks"
    template: str = "template"
    total: str = "total"
    translate: str = "translate"
    ungrib: str = "ungrib"
    updatefile: str = "update_file"
    updatefmt: str = "update_format"
    upp: str = "upp"
    validate: str = "validate"
    valsfile: str = "values_file"
    valsfmt: str = "values_format"
    valsneeded: str = "values_needed"
    verbose: str = "verbose"
    version: str = "version"
    ww3: str = "ww3"
