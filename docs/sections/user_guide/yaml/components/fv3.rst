.. _fv3_yaml:

fv3
===

Structured YAML to run FV3 is validated by JSON Schema and requires the ``fv3:`` block, described below. If FV3 is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required. The configuration files required by the UFS Weather Model are documented :weather-model-io:`here<model-configuration-files>`.

.. include:: /shared/injected_cycle.rst

Here is a prototype UW YAML ``fv3:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/fv3.yaml

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

See :ref:`this page <execution_yaml>` for details.

field_table:
^^^^^^^^^^^^

The path to a :weather-model-io:`valid field-table file<field-table-file>` to be copied into the run directory.

.. include:: /shared/stager.rst

lateral_boundary_conditions:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Describes how the lateral boundary conditions have been prepared for a limited-area configuration of the FV3 forecast. Required when ``domain`` is ``regional``.

  **interval_hours:**

  How frequently the lateral boundary conditions will be used in the FV3 forecast, in integer hours.

  **offset:**

  How many hours earlier the external model used for boundary conditions started compared to the desired forecast cycle, in integer hours.

  **path:**

  An absolute-path template to the lateral boundary condition files prepared for the forecast. The Python ``int`` variable ``forecast_hour`` will be interpolated into, e.g., ``/path/to/srw.t00z.gfs_bndy.tile7.f{forecast_hour:03d}.nc``. Note that this is a Python string template rather than a Jinja2 template.

length:
^^^^^^^

The length of the forecast in integer hours.

model_configure:
^^^^^^^^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details). See FV3 ``model_configure`` documentation :weather-model-io:`here<model-configure-file>`.

namelist:
^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details). See FV3 ``model_configure`` documentation :weather-model-io:`here<namelist-file-input-nml>`.

.. include:: /shared/validate_namelist.rst

rundir:
^^^^^^^

The path to the run directory.
