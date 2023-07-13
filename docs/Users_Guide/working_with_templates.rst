.. _working_with_templates:

**************************
Working with Templates 
**************************

.. _atp_j2:

---------------------
atparse_to_jinja2
---------------------

This tool turns any *atparse*-enabled template into a Jinja2-enabled template. For example, the following is an *atparse*-enabled template::

  $ WAVEWATCH III multi-grid input file
  $ ------------------------------------
   @[NMGRIDS] @[NFGRIDS] @[FUNIPNT] @[IOSRV] @[FPNTPROC] @[FGRDPROC]
  $
  @[CPLILINE]
  @[WINDLINE]
  @[ICELINE]
  @[CURRLINE]
  @[UNIPOINTS]
  @[WW3GRIDLINE]
  $
     @[RUN_BEG]   @[RUN_END]
  $
     @[FLAGMASKCOMP]  @[FLAGMASKOUT]
  $

``atparse_to_jinja2`` is called on the template from the command line::

  python scripts/atparse_to_jinja2.py -i /<path-to-template>/enabled_template.inp.IN -o <path-to-outfile>/jinja2template.nml

The resulting Jinja2-enabled template is written to the specified outfile, ``jinja2template.nml``::

  $ WAVEWATCH III multi-grid input file
  $ ------------------------------------
   {{NMGRIDS}} {{NFGRIDS}} {{FUNIPNT}} {{IOSRV}} {{FPNTPROC}} {{FGRDPROC}}
  $
  {{CPLILINE}}
  {{WINDLINE}}
  {{ICELINE}}
  {{CURRLINE}}
  {{UNIPOINTS}}
  {{WW3GRIDLINE}}
  $
     {{RUN_BEG}}   {{RUN_END}}
  $
     {{FLAGMASKCOMP}}  {{FLAGMASKOUT}}
  $
  
The created ``jinja2template.nml`` file can also now be used with the ``templater.py`` tool.

.. _templater.py:

----------------
templater.py
----------------

``templater.py`` takes in any Jinja2 template file and renders it with user-supplied values. ``templater.py`` takes several command line arguments, including the path to the Jinja2 template file, an optional 
path to a YAML configuration file, and any additional configuration settings which will override values found in the YAML 
configuration (config) file or user environment variables.  If the provided config settings do not contain values for every field in the input Jinja2 template file, ``templater.py`` will return an error.

.. _temp_inp_conf:

^^^^^^^^^^^^^^^^^^^^^^^^^^
Input file and config file
^^^^^^^^^^^^^^^^^^^^^^^^^^
Here is an example template file, ``jinja2template.nml``::

  $ WAVEWATCH III multi-grid input file
  $ ------------------------------------
   {{NMGRIDS}} {{NFGRIDS}} {{FUNIPNT}} {{IOSRV}} {{FPNTPROC}} {{FGRDPROC}}
  $
  {{CPLILINE}}
  {{WINDLINE}}
  {{ICELINE}}
  {{CURRLINE}}
  {{UNIPOINTS}}
  {{WW3GRIDLINE}}
  $
     {{RUN_BEG}}   {{RUN_END}}
  $
     {{FLAGMASKCOMP}}  {{FLAGMASKOUT}}
  $

And here is the example YAML config file we want to use to update the values in the template::

  NMGRIDS: 3
  NFGRIDS: 1
  FUNIPNT: ' T'
  IOSRV: 1
  FPNTPROC: 'T'
  FGRDPROC: ' T'
  CPLILINE: "'glo_15mxt'"
  WINDLINE: '$'
  ICELINE: '$'
  CURRLINE: '$'
  UNIPOINTS: 'ww3'
  WW3GRIDLINE: "'ww3' 'no' 'no' 'CPL:native' 'no' 'no' 'no' 'no' 'no' 'no'  1  1  0.00 1.00  F"
  RUN_BEG: 0000.00.00.00:00
  RUN_END: 0000.00.00.00:00
  FLAGMASKCOMP:  ' F'
  FLAGMASKOUT: ' F'

To run ``templater.py`` with an input template file and a config file, modify the following command::

    python scripts/templater.py -i /<path-to-template>/jinja2template.nml -c /<path-to-config>/example_config.yaml -o <path-to-outfile>/rendered_template.nml

where:

   * ``-i`` refers to the input template file
   * ``-c`` refers to the config file
   * ``-o`` refers to the output file (or outfile)

The rendered template will be updated with the values contained in the config file::

  $ WAVEWATCH III multi-grid input file
  $ ------------------------------------
   3 1  T 1 T  T
  $
  'glo_15mxt'
  $
  $
  $
  ww3
  'ww3' 'no' 'no' 'CPL:native' 'no' 'no' 'no' 'no' 'no' 'no'  1  1  0.00 1.00  F
  $
     0000.00.00.00:00   0000.00.00.00:00
  $
      F   F
  $

.. _temp_inp_env:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Input file and environment file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If ``templater.py`` is called on an input file, but no config file is provided, the template will be rendered using the user environment (``os.environ``).

.. _temp_inp_cli:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Input file and command line config items
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``templater.py`` can be run with an input file and config items provided through the command line by using the ``config_items`` flag::

    python scripts/templater.py -i /<path-totemplate>/jinja2template.nml NFGRIDS=0 NMGRIDS=5 FUNIPNT=' T' IOSRV='None' FPNTPROC='None' FGRDPROC=' None' CPLILINE='glo_15mxt' WINDLINE='$' ICELINE='$' CURRLINE='$' UNIPOINTS='ww3' WW3GRIDLINE="'ww3' 'no' 'no' 'CPL:native' 'no' 'no' 'no' 'no' 'no' 'no'  1  1  0.00 1.00  F" RUN_BEG=0000.00.00.00:00 RUN_END=0000.00.00.00:00 FLAGMASKCOMP=' F' FLAGMASKOUT=' F'

Rendered template::

  $ WAVEWATCH III multi-grid input file
  $ ------------------------------------
    0, 5, T, None, None,  None
  $
  'glo_15mxt'
  $
  $
  $
  ww3
  'ww3' 'no' 'no' 'CPL:native' 'no' 'no' 'no' 'no' 'no' 'no'  1  1  0.00 1.00  F
  $
     0000.00.00.00:00   0000.00.00.00:00
  $
      F   F
  $

Any configuration settings supplied through the ``config_items`` flag will override values found in the config file or user environment.

.. _temp_dryrun:

^^^^^^^^^^^^
dry_run flag
^^^^^^^^^^^^
Running ``templater.py`` with the ``-d`` or ``--dry-run`` flag will print the rendered template to stdout only and provide no other output::

    python scripts/templater.py -i /<path-totemplate>/jinja2template.nml -c /<path-to-config>/example_config.yaml -d

  ----------------------------------------------------------------------
  ----------------------------------------------------------------------
          outfile: None
   input_template: /<path-totemplate>/jinja2template.nml
      config_file: /<path-to-config>/example_config.yaml
     config_items: []
          dry_run: True
    values_needed: False
          verbose: False
            quiet: False
  ----------------------------------------------------------------------
  ----------------------------------------------------------------------
  $ WAVEWATCH III multi-grid input file
  $ ------------------------------------
   3 1  T 1 T  T
  $
  'glo_15mxt'
  $
  $
  $
  ww3
  'ww3' 'no' 'no' 'CPL:native' 'no' 'no' 'no' 'no' 'no' 'no'  1  1  0.00 1.00  F
  $
     0000.00.00.00:00   0000.00.00.00:00
  $
      F   F
  $

     N
   

.. _temp_val_needed:

^^^^^^^^^^^^^^^^^^
Values Needed Flag
^^^^^^^^^^^^^^^^^^
If provided, the ``--values-needed`` flag will print a list of required configuration settings for the input template to stdout::
    
  workflow-tools % python scripts/templater.py -i /<path-totemplate>/jinja2template.nml --values-needed
  Running script templater.py with args:
  ----------------------------------------------------------------------
  ----------------------------------------------------------------------
          outfile: None
   input_template: /<path-totemplate>/jinja2template.nml
      config_file: None
     config_items: []
          dry_run: False
    values_needed: True
          verbose: False
            quiet: False
  ----------------------------------------------------------------------
  ----------------------------------------------------------------------
  Values needed for this template are:
  CPLILINE
  CURRLINE
  FGRDPROC
  FLAGMASKCOMP
  FLAGMASKOUT
  FPNTPROC
  FUNIPNT
  ICELINE
  IOSRV
  NFGRIDS
  NMGRIDS
  RUN_BEG
  RUN_END
  UNIPOINTS
  WINDLINE
  WW3GRIDLINE
