.. _forecast_yaml:

Forecast YAML
=============

The structured YAML to run a forecast is described below. It is enforced via JSON Schema.

In this section, there are entries that define where the forecast will run (``run_directory:``), what will run (``executable:``), the data files that should be staged (``cycle_dependent:`` and ``static:``), and blocks that correspond to the configuration files required by the forecast model (``fd_ufs:``, ``field_table:``, ``namelist:``, etc.). Each of the configuration file blocks will allow the user to set a template file as input, or to define a configuration file in its native key/value pair format with an option to update the values (``update_values:``) contained in the original input file (``base_file:``).

The configuration files required by the UFS Weather Model are documented :weather-model-io:`here<model-configuration-files>`.

The ``forecast:`` section
-------------------------

This section describes the specifics of the FV3 atmosphere forecast component.

.. code-block:: yaml

  forecast:
    cycle_dependent:
      INPUT/gfs_data.nc: /path/to/gfs_data.nc
      INPUT/sfc_data.nc: /path/to/sfc_data.nc
      INPUT/gfs_ctrl.nc: /path/to/gfs_ctrl.nc
    diag_table:
      template_file: /path/to/diag_table/template/file
    domain: regional
    executable: fv3.exe
    fd_ufs:
      base_file: /path/to/base/fd_ufs.yaml
    field_table:
      base_file: /path/to/field_table.yaml
      update_values:
        liq_wat:
          longname: cloud water mixing ratio
          units: kg/kg
          profile_type:
            name: fixed
            surface_value: 2.0
    length: 12
    model_configure:
      base_file: /path/to/base/model_configure
      update_values:
        write_dopost: .false.
    namelist:
      base_file: /path/to/base/input.nml
      update_values:
        fv_core_nml:
          k_split: 2
          n_split: 6
    nems.configure:
      template_file: /path/to/template/nems.configure
    run_dir: /path/to/forecast/run/directory/{yyyymmddhh}
    static:
      fv3.exe: /path/to/executable/ufs_model
      INPUT/grid_spec.nc: /path/to/grid_spec.nc
      ...
      data_table: /path/to/data_table
      eta_micro_lookup.data: /path/to/noahmptable.dat
      noahmptable.tbl: /path/to/noahmptable.tbl

.. _updating_values:

Updating Values
^^^^^^^^^^^^^^^

Many of the sections describe configuration files needed by the UFS Weather Model, i.e. ``namelist:``, ``fd_ufs:``, ``model_configure:``. The ``base_file:`` sub-entry is required to initially stage the file; it can then be modified via an ``update_values:`` block.

To ensure the correct values are updated, all keys that act as section headers above the entry to be updated need to be provided in the order in which they appear in the base file. Multiple entries within a block may be updated and they need not follow the same order as those in the base file. For example, the base file named ``people.yaml`` may contain:

.. code-block:: yaml

   person:
     age: 19
     address:
       city: Boston
       number: 12
       state: MA
       street: Acorn St
     name: Jane

Then the entries under the YAML section would edit this base file with the entries:

.. code-block:: yaml

   base_file: people.yaml
   update_values:
     person:
       address:
         street: Main St
         number: 99

Rendering Template Files
^^^^^^^^^^^^^^^^^^^^^^^^

Requires a path to a template file in the ``template_file:`` entry. There is no option to add values in the YAML. Instead, the driver is programmed to enter necessary values for the template.

UW YAML Keys
^^^^^^^^^^^^

``cycle_dependent:``
""""""""""""""""""""

This block contains a set of files to stage in the run directory: File names as they appear in the run directory are keys and their source paths are the values. Source paths can be provided as a single string path, or a list of paths to be staged in a common directory under their original names.

  .. warning:: The current version does not support adding cycle information to the content of the files, and this information must be hard-coded in the YAML file.

``diag_table:``
"""""""""""""""

In ``uwtools``, the ``diag_table`` is treated as a template so that the date and time information in the header may be filled in appropriately. The ``template_file:`` is the path to the input Jinja2 template. Date information is provided on the command line or via API interfaces.

The diag_table is described :weather-model-io:`here<diag-table-file>`.

``domain:``
"""""""""""

A switch to differentiate between a global or regional configuration. Accepted values are ``global`` and ``regional``.

``executable:``
"""""""""""""""

The path to the compiled executable.

``fd_ufs:``
""""""""""""

The section requires a ``base_file:`` entry that contains the path to the YAML file. An optional ``update_values:`` section may be provided to update any values contained in the base file. Please see the :ref:`updating_values` section for providing information in these entries.

The ``fd_ufs.yaml`` file is a structured YAML used by the FV3 weather model. The tested version can be found in the :ufs-weather-model:`ufs-weather-model repository<blob/develop/tests/parm/fd_ufs.yaml>`. The naming convention for the dictionary entries are documented :cmeps:`here<>`.

``field_table:``
""""""""""""""""

The section requires a ``base_file:`` entry that contains the path to the YAML file. An optional ``update_values:`` section may be provided to update any values contained in the base file. Please see the :ref:`updating_values` section for providing information in these entries.

If a pre-defined field table (i.e., not a configurable YAML) is to be used, include it in the ``static:`` section.

The documentation for the ``field_table`` file is :weather-model-io:`here<field-table-file>`. Information on how to structure the UW YAML for configuring a ``field_table`` is in the :ref:`defining_a_field_table` Section.

``length:``
"""""""""""

The length of the forecast in hours.

``model_configure:``
""""""""""""""""""""

The section requires a ``base_file:`` entry that contains the path to the YAML file. An optional ``update_values:`` section may be provided to update any values contained in the base file. Please see the :ref:`updating_values` section for providing information in these entries.

The documentation for the ``model_configure`` file is :weather-model-io:`here<model-configure-file>`.

``namelist:``
"""""""""""""

The section requires a ``base_file:`` entry that contains the path to the YAML file. An optional ``update_values:`` section may be provided to update any values contained in the base file. Please see the :ref:`updating_values` section for providing information in these entries.

The documentation for the FV3 namelist, ``input.nml`` is :weather-model-io:`here<namelist-file-input-nml>`.

``run_dir:``
""""""""""""

The path where the forecast input data will be staged and output data will appear after a successful forecast.

``static:``
"""""""""""

This block contains a set of files to stage in the run directory: file names as they appear in the run directory are keys and their source paths are the values. Source paths can be provided as a single string path, or a list of paths to be staged in a common directory under their original names.

``ufs_configure:``

"""""""""""""""""""

In ``uwtools``, the ``ufs.configure`` file is treated as a template so that the date and time information in the header may be filled in appropriately. The ``template_file:`` is the path to the input Jinja2 template. There is no option to add values in the YAML. Instead, the driver is programmed to enter necessary values for the template.

The documentation for the ``ufs.configure`` file is :weather-model-io:`here<ufs-configure-file>`.

The ``platform:`` section
-------------------------

This section describes necessary facts about the computational platform.

.. code-block:: yaml

  platform:
    mpicmd: srun # required
    scheduler: slurm

``mpicmd:``
^^^^^^^^^^^
The MPI command used to run the model executable. Typical options are ``srun``, ``mpirun``, ``mpiexec``, etc. System administrators should be able to advise the appropriate choice, if needed.

``scheduler:``
^^^^^^^^^^^^^^
The name of the batch system. Supported options are ``lfs``, ``pbs``, and ``slurm``.

The ``preprocessing:`` section
------------------------------

.. code-block:: yaml

  preprocessing:
    lateral_boundary_conditions:
      interval_hours: 3 # optional, default
      offset: 0 # optional, default
      output_file_path: # required

``lateral_boundary_conditions:``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The optional section describes how the lateral boundary conditions have been prepared for a limited-area configuration of the model forecast. It is required for a limited-area forecast. The following entries in its subtree are used for the forecast:

``interval_hours:``
"""""""""""""""""""
The integer number of hours setting how frequently the lateral boundary conditions will be used in the model forecast.

``offset:``
"""""""""""
The integer number of hours setting how many hours earlier the external model used for boundary conditions started compared to the desired forecast cycle.

``output_file_path:``
"""""""""""""""""""""""""
The path to the lateral boundary conditions files prepared for the forecast. It accepts the integer ``forecast_hour`` as a Python template, e.g., ``/path/to/srw.t00z.gfs_bndy.tile7.f{forecast_hour:03d}.nc``.

The ``user:`` section
---------------------

.. code-block:: yaml

  user:
    account: my_account # optional

``account:``
^^^^^^^^^^^^
The user account associated with the batch system.
