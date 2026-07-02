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

    ECF_HOME: str = _
    ECF_HOST: str = _
    ECF_LOG: str = _
    ECF_NAME: str = _
    ECF_PASS: str = _
    ECF_PORT: str = _
    ECF_SSL: str = _
    ECF_TRYNO: str = _
    account: str = _
    action: str = _
    base_file: str = _
    batch: str = _
    batchargs: str = _
    cdeps: str = _
    chgres_cube: str = _
    classname: str = _
    compare: str = _
    compose: str = _
    config: str = _
    config_file: str = _
    configs: str = _
    copy: str = _
    cycle: str = _
    database: str = _
    date: str = _
    datelist: str = _
    datetime: str = _
    day: str = _
    defstatus: str = _
    dry_run: str = _
    ecflow: str = _
    end: str = _
    enkf: str = _
    enumerated: str = _
    env: str = _
    envcmds: str = _
    esg_grid: str = _
    events: str = _
    executable: str = _
    execute: str = _
    execution: str = _
    expand: str = _
    extern: str = _
    fallback: str = _
    families: str = _
    family: str = _
    file: str = _
    filter_topo: str = _
    format1: str = _
    format2: str = _
    fs: str = _
    fv3: str = _
    global_equiv_resol: str = _
    graph_file: str = _
    gsi: str = _
    hardlink: str = _
    help: str = _
    hostname: str = _
    hsi: str = _
    htar: str = _
    incantation: str = _
    inlimits: str = _
    input_file: str = _
    input_format: str = _
    insecure: str = _
    int: str = _
    ioda: str = _
    iterate: str = _
    jedi: str = _
    key_eq_val_pairs: str = _
    key_path: str = _
    labels: str = _
    late: str = _
    leadtime: str = _
    limits: str = _
    link: str = _
    list: str = _
    make_hgrid: str = _
    make_solo_mosaic: str = _
    makedirs: str = _
    manual: str = _
    meters: str = _
    mode: str = _
    module: str = _
    mpas: str = _
    mpas_init: str = _
    mpassit: str = _
    mpiargs: str = _
    mpicmd: str = _
    namelist: str = _
    node: str = _
    notready: str = _
    orog: str = _
    orog_gsl: str = _
    output_dir: str = _
    output_file: str = _
    output_format: str = _
    parent: str = _
    path1: str = _
    path2: str = _
    platform: str = _
    port: str = _
    post_includes: str = _
    pre_includes: str = _
    properties: str = _
    quiet: str = _
    rate: str = _
    ready: str = _
    realize: str = _
    refs: str = _
    render: str = _
    repeat: str = _
    report: str = _
    rocoto: str = _
    run: str = _
    rundir: str = _
    scheduler: str = _
    schema_file: str = _
    schism: str = _
    script: str = _
    scripts_dir: str = _
    search_path: str = _
    server: str = _
    sfc_climo_gen: str = _
    shave: str = _
    show_schema: str = _
    stacksize: str = _
    start: str = _
    stdout: str = _
    step: str = _
    string: str = _
    suite: str = _
    suitedef: str = _
    suites: str = _
    symlink: str = _
    target_dir: str = _
    task: str = _
    tasks: str = _
    template: str = _
    threads: str = _
    total: str = _
    translate: str = _
    trigger: str = _
    ungrib: str = _
    update_file: str = _
    update_format: str = _
    update_values: str = _
    upp: str = _
    upp_assets: str = _
    url_scheme_file: str = "file"
    url_scheme_hsi: str = "hsi"
    url_scheme_htar: str = "htar"
    url_scheme_http: str = "http"
    url_scheme_https: str = "https"
    validate: str = _
    validate_xml: str = "validate-xml"
    values_file: str = _
    values_format: str = _
    values_needed: str = _
    variable: str = _
    vars: str = _
    verbose: str = _
    version: str = _
    workflow: str = _
    ww3: str = _


# Public

FORMAT = _FORMAT()
STR = _STR()
