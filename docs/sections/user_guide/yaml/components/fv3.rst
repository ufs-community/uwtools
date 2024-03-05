.. _fv3_yaml:

fv3
===

Structured YAML to run FV3 is validated by JSON Schema and requires the ``fv3:`` block, described below. If FV3 is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required. The configuration files required by the UFS Weather Model are documented :weather-model-io:`here<model-configuration-files>`.

The ``fv3:`` Block
------------------

Here is a prototype UW YAML ``fv3:`` block, explained in detail below:

.. code-block:: yaml

   fv3:
     diag_table: /path/to/diag_table_to_use
     domain: regional
     execution:
       batchargs:
         walltime: "00:10:00"
       executable: ufs_model
       mpiargs:
         - "--export=NONE"
       mpicmd: srun
       threads: 1
     field_table:
       base_file: /path/to/field_table_to_use
       update_values:
         liq_wat:
           longname: cloud water mixing ratio
           units: kg/kg
           profile_type:
             name: fixed
             surface_value: 2.0
     files_to_copy:
       INPUT/gfs_data.nc: /path/to/gfs_data.nc
       INPUT/sfc_data.nc: /path/to/sfc_data.nc
       INPUT/gfs_ctrl.nc: /path/to/gfs_ctrl.nc
       ...
     files_to_link:
       co2historicaldata_2010.txt: src/uwtools/drivers/global_co2historicaldata_2010.txt
       co2historicaldata_2011.txt: src/uwtools/drivers/global_co2historicaldata_2011.txt
       ...
     lateral_boundary_conditions:
       interval_hours: 3
       offset: 0
       path: gfs_bndy.tile{tile}.f{forecast_hour}.nc
     length: 12
     model_configure:
       base_file: /path/to/model_configure_to_use
       update_values:
         write_dopost: .false.
     namelist:
       base_file: /path/to/base/input.nml
       update_values:
         fv_core_nml:
           k_split: 2
           n_split: 6
     run_dir: /path/to/runs/{{ cycle.strftime('%Y%m%d%H') }}

UW YAML for the ``fv3:`` Block
------------------------------

diag_table:
^^^^^^^^^^^

The path to the ``diag_table`` file. It does not currently support edits, so must be pre-configured as needed. See FV3 ``diag_table`` documentation :weather-model-io:`here<diag-table-file>`.

domain:
^^^^^^^

Accepted values are ``global`` and ``regional``.

execution:
^^^^^^^^^^

See :ref:`here <execution_yaml>` for details.

field_table:
^^^^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see the :ref:`updating_values` for details). See FV3 ``field_table`` documentation :weather-model-io:`here<field-table-file>`, or :ref:`defining_a_field_table` for UW YAML-specific details.

files_to_copy:
^^^^^^^^^^^^^^

Defines files to be copied to the run directory. Keys in the ``files_to_copy:`` YAML map specify destination paths relative to the run directory, and values specify source paths. Both keys and values may contain Jinja2 variables/expressions using a ``cycle`` variable, which is a Python ``datetime`` object corresponding to the FV3 cycle being run. This supports specification of cycle-specific filenames/paths. For example, a key-value pair

.. code-block:: yaml

   gfs.t{{ cycle.strftime('%H') }}z.atmanl.nc: /some/path/{{ cycle.strftime('%Y%m%d')}}/{{ cycle.strftime('%H') }}/gfs.t{{ cycle.strftime('%H') }}z.atmanl.nc

would be rendered as

.. code-block:: yaml

   gfs.t18z.atmanl.nc: /some/path/20240212/18/gfs.t18z.atmanl.nc

for the ``2024-02-12T18`` cycle.

files_to_link:
^^^^^^^^^^^^^^

Identical to ``files_to_copy:`` except that symbolic links will be created in the run directory instead of copies.


lateral_boundary_conditions:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Describes how the lateral boundary conditions have been prepared for a limited-area configuration of the FV3 forecast.

interval_hours:
"""""""""""""""

How frequently the lateral boundary conditions will be used in the FV3 forecast, in integer hours.

offset:
"""""""

How many hours earlier the external model used for boundary conditions started compared to the desired forecast cycle, in integer hours.

path:
"""""

An absolute-path template to the lateral boundary condition files prepared for the forecast. The Python ``int`` variable ``forecast_hour`` will be interpolated into, e.g., ``/path/to/srw.t00z.gfs_bndy.tile7.f{forecast_hour:03d}.nc``. Note that this is a Python string template rather than a Jinja2 template.

length:
^^^^^^^

The length of the forecast in integer hours.

model_configure:
^^^^^^^^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see the :ref:`updating_values` for details). See FV3 ``model_configure`` documentation :weather-model-io:`here<model-configure-file>`.

namelist:
^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see the :ref:`updating_values` for details). See FV3 ``model_configure`` documentation :weather-model-io:`here<namelist-file-input-nml>`.

run_dir:
^^^^^^^^

The path to the directory where FV3 will find its inputs, configuration files, etc., and where it will write its output.
