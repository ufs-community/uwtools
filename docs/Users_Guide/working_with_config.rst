.. _working_with_config:

******************************************
Working with Standard Configuration Files
******************************************

.. _set_config.py:

-------------
set_config.py
-------------

This tool transforms a "base" config file into a fully formed, app-ready file that is fully configurable by the end user.

.. _conf_inp_conf:

^^^^^^^^^^^^^^^^^^^^^^^^^^
Input file and config file
^^^^^^^^^^^^^^^^^^^^^^^^^^

``set_config.py`` determines the input file type and creates a configuration object based on the input file type. If a user-defined configuration file is provided, it creates a configuration object for the user-defined configuration file and updates the values in the input configuration object.

Sample input base file::

  fruit: papaya
  vegetable: eggplant
  how_many: 17
  dressing: ranch

Sample config file::

  fruit: papaya
  how_many: 17
  topping: crouton
  size: large
  meat: chicken

To run ``set_config.py`` with an input and config file::

    python scripts/set_config.py -i /<path-to-input-file>/sample_base.yaml -c /<path-to-config-file>/sample_config.yaml -o /<path-to-outfile>/sample_outfile.yaml

The output is a fully formed config file:: 

  fruit: papaya
  vegetable: eggplant
  how_many: 17
  dressing: ranch
  topping: crouton
  size: large
  meat: chicken

.. _conf_field:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Generating a field table from YAML
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To generate a field table from a YAML config base file using ``set_config.py``, the outfile must include ``field_table`` in the outfile name. 

YAML base file::

  sphum:
    longname: specific humidity
    units: kg/kg
    profile_type: 
      name: fixed
      surface_value: 1.e30
  liq_wat:
    longname: cloud water mixing ratio
    units: kg/kg
    profile_type: 
      name: fixed
      surface_value: 1.e30
  rainwat:
    longname: rain mixing ratio
    units: kg/kg
    profile_type: 
      name: fixed
      surface_value: 1.e30
      
Command with ``field_table`` outfile type specified::     

    python scripts/set_config.py -i /<path-to-input-file>/sample_base_field.yaml -o /<path-to-outfile>/sample_field_table.FV3_GFS_v16
    
Generated field table::

   "TRACER", "atmos_mod", "sphum"
             "longname", "specific humidity"
             "units", "kg/kg"
         "profile_type", "fixed", "surface_value=1.e30" /
   "TRACER", "atmos_mod", "liq_wat"
             "longname", "cloud water mixing ratio"
             "units", "kg/kg"
         "profile_type", "fixed", "surface_value=1.e30" /
   "TRACER", "atmos_mod", "rainwat"
             "longname", "rain mixing ratio"
             "units", "kg/kg"
         "profile_type", "fixed", "surface_value=1.e30" /
   
.. _conf_dry:

^^^^^^^^^^^^
dry_run flag
^^^^^^^^^^^^

Running ``set_config.py`` with ``-d`` or ``--dry-run`` will print the config object to stdout only and provide no other output::

        python scripts/set_config.py -i /<path-to-input-file>/sample_base.yaml -c /<path-to-config-file>/sample_config.yaml --dry-run

The command above will generate the following output in the command line::

  {"fruit": "papaya", "vegetable": "eggplant", "how_many": 17, "dressing": "ranch", "topping": "crouton", "size": "large", "meat": "chicken"}

If the ``--dry-run`` flag is run with a user outfile included, it will generate a warning that the outfile will not be written.

.. _conf_val_needed:

^^^^^^^^^^^^^^^^^^
values_needed flag
^^^^^^^^^^^^^^^^^^

If provided, the ``values-needed`` flag will print to the stdout a list of which keys in the created config object are complete, which keys contain unfilled jinja templates, and which keys are set to empty. Config objects with nested keys will print a path to each key. Given the following YAML config object::

  FV3GFS:
    nomads:
      protocol: download
      url: https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{{ yyyymmdd }}/{{ hh }}/atmos
      file_names: &gfs_file_names
        grib2:
          anl:
            - gfs.t{{ hh }}z.atmanl.nemsio
            - gfs.t{{ hh }}z.sfcanl.nemsio
          fcst:
            - gfs.t{{ hh }}z.pgrb2.0p25.f{{ fcst_hr03d }}

        nemsio: Null
        testfalse: False
        testzero: 0
      testempty:

the command:: 

  python scripts/set_config.py -i /<path-to-input-file>/sample_base.yaml -c /<path-to-config-file>/sample_config.yaml --values-needed
  
will print the following to the stdout::

  Keys that are complete:
      FV3GFS
      FV3GFS.nomads
      FV3GFS.nomads.protocol
      FV3GFS.nomads.file_names
      FV3GFS.nomads.file_names.grib2
      FV3GFS.nomads.file_names.testfalse
      FV3GFS.nomads.file_names.testzero

  Keys that have unfilled jinja2 templates:
      FV3GFS.nomads.url
      FV3GFS.nomads.file_names.grib2.anl
      FV3GFS.nomads.file_names.grib2.fcst

  Keys that are set to empty:
      FV3GFS.nomads.file_names.nemsio
      FV3GFS.nomads.testempty

.. _conf_conversion:

^^^^^^^^^^^^^^^^
Conversion flags
^^^^^^^^^^^^^^^^

``set_config.py`` has three flags that will convert given input, config, or outfile to the user-provided file type::
    --input-file-type
    --config-file-type
    --outfile-file-type

``--input-file-type`` and ``--config-file-type`` accept YAML ('YAML'), bash/ini ('INI'), or namelist ('F90') file types; ``--outfile-file-type`` accepts these three as well as field table ('FieldTable').  This tool requires that the given file (input, config, or outfile) have a compatible structure with the provided file type.  A YAML file can have any depth, a bash/ini file can have a depth of 1 or 2, and a namelist file must have a depth of 2.

.. _conf_compare:

^^^^^^^^^^^^
Compare flag
^^^^^^^^^^^^

When run with the ``--compare`` flag, ``set_config.py`` will print the difference between the input file (``-i``) and the config file (``-c``) to the stdout.
