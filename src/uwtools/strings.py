"""
Canonical strings used throughout uwtools.
"""

# This module provides containers for string literals used throughout the codebase, organized by
# the source of their definition. Most values are dynamically set to match the key, but explicit
# values can also be provided when the key and value should not be the same. This mechanism reduces
# the risk of typos in string literals, and exposes references to the type checker for validation.

from dataclasses import dataclass, fields

# Private

_ = ""  # default value, to be replaced by key


class _ValsMatchKeys:
    def __post_init__(self):
        attr = "__dataclass_fields__"
        fields = getattr(self, attr).values()
        for field in fields:
            if not getattr(self, field.name):
                object.__setattr__(self, field.name, field.name)


@dataclass(frozen=True)
class _EC(_ValsMatchKeys):
    """
    EcFlow-specific string constants.
    """

    account: str = _
    config: str = _
    date: str = _
    datelist: str = _
    datetime: str = _
    day: str = _
    defstatus: str = _
    enumerated: str = _
    envcmds: str = _
    events: str = _
    execution: str = _
    expand: str = _
    extern: str = _
    families: str = _
    family: str = _
    inlimits: str = _
    int: str = _
    jobcmd: str = _
    labels: str = _
    late: str = _
    limits: str = _
    manual: str = _
    meters: str = _
    node: str = _
    parent: str = _
    post_includes: str = _
    pre_includes: str = _
    refs: str = _
    repeat: str = _
    rundir: str = _
    scheduler: str = _
    script: str = _
    string: str = _
    suite: str = _
    suites: str = _
    task: str = _
    tasks: str = _
    trigger: str = _
    vars: str = _


@dataclass(frozen=True)
class _FORMAT(_ValsMatchKeys):
    """
    Format names.
    """

    atparse: str = _
    bash: str = "sh"
    cfg: str = "ini"
    fieldtable: str = _
    ini: str = _
    jinja2: str = _
    nml: str = _
    sh: str = _
    yaml: str = _
    yml: str = "yaml"

    @staticmethod
    def extensions() -> list[str]:
        """
        Return recognized filename extensions.
        """
        return [FORMAT.ini, FORMAT.nml, FORMAT.sh, FORMAT.yaml]

    @staticmethod
    def formats() -> dict[str, str]:
        """
        Return the recognized format names.
        """
        return {
            field.name: str(getattr(FORMAT, field.name))
            for field in fields(FORMAT)
            if not field.name.startswith("_")
        }


@dataclass(frozen=True)
class _STR(_ValsMatchKeys):
    """
    General strings.
    """

    account: str = _
    action: str = _
    basefile: str = "base_file"
    batch: str = _
    batchargs: str = _
    cdeps: str = _
    cfgfile: str = "config_file"
    chgrescube: str = "chgres_cube"
    classname: str = _
    compare: str = _
    compose: str = _
    config: str = _
    configs: str = _
    copy: str = _
    cycle: str = _
    database: str = _
    dryrun: str = "dry_run"
    ecflow: str = _
    enkf: str = _
    env: str = _
    envcmds: str = _
    esggrid: str = "esg_grid"
    executable: str = _
    execute: str = _
    execution: str = _
    fallback: str = _
    file: str = _
    filtertopo: str = "filter_topo"
    fmt1: str = "format1"
    fmt2: str = "format2"
    fs: str = _
    fv3: str = _
    globalequivresol: str = "global_equiv_resol"
    graphfile: str = "graph_file"
    gsi: str = _
    hardlink: str = _
    help: str = _
    hsi: str = _
    htar: str = _
    infile: str = "input_file"
    infmt: str = "input_format"
    ioda: str = _
    iterate: str = _
    jedi: str = _
    keypath: str = "key_path"
    keyvalpairs: str = "key_eq_val_pairs"
    leadtime: str = _
    link: str = _
    makedirs: str = _
    makehgrid: str = "make_hgrid"
    makesolomosaic: str = "make_solo_mosaic"
    mode: str = _
    model: str = _
    module: str = _
    mpas: str = _
    mpasinit: str = "mpas_init"
    mpassit: str = _
    mpiargs: str = _
    mpicmd: str = _
    namelist: str = _
    notready: str = "not-ready"
    orog: str = _
    oroggsl: str = "orog_gsl"
    outfile: str = "output_file"
    outfmt: str = "output_format"
    path1: str = _
    path2: str = _
    platform: str = _
    properties: str = _
    quiet: str = _
    rate: str = _
    ready: str = _
    realize: str = _
    render: str = _
    report: str = _
    rocoto: str = _
    run: str = _
    rundir: str = _
    scheduler: str = _
    schemafile: str = "schema_file"
    schism: str = _
    searchpath: str = "search_path"
    sfcclimogen: str = "sfc_climo_gen"
    shave: str = _
    showschema: str = "show_schema"
    stacksize: str = _
    stdout: str = _
    symlink: str = _
    targetdir: str = "target_dir"
    task: str = _
    tasks: str = _
    template: str = _
    threads: str = _
    total: str = _
    translate: str = _
    ungrib: str = _
    updatefile: str = "update_file"
    updatefmt: str = "update_format"
    updatevalues: str = "update_values"
    upp: str = _
    upp_assets: str = _
    url_scheme_file: str = "file"
    url_scheme_hsi: str = "hsi"
    url_scheme_htar: str = "htar"
    url_scheme_http: str = "http"
    url_scheme_https: str = "https"
    validate: str = _
    valsfile: str = "values_file"
    valsfmt: str = "values_format"
    valsneeded: str = "values_needed"
    verbose: str = _
    version: str = _
    workflow: str = _
    ww3: str = _


# Public

EC = _EC()
FORMAT = _FORMAT()
STR = _STR()
