.. _defining_a_field_table:

Defining a ``field_table``
==========================

The :ufs-weather-model:`UFS Weather Model<>` requires as one of its input files (:weather-model-io:`documented here<model-configuration-files>`) a ``field_table`` file. While the format required by the ufs-weather-model is not a YAML file, with ``uwtools`` package, the ``field_table`` entries may be managed as a YAML file, and written to the expected structure (:weather-model-io:`documented here<field-table-file>`).

To generate a given ``field_table`` entry with the form:

.. code-block:: text

   "TRACER", "atmos_mod", "sphum"
             "longname",     "specific humidity"
             "units",        "kg/kg"
             "profile_type", "fixed", "surface_value=3.e-6" /

Entries can be manage in YAML with the form:

.. code-block:: text

   sphum:
     longname: "specific humidity"
     units: kg/kg
     profile_type:
       name: fixed
       surface_value: 3.e-6


Additional tracers may be added at the same level of YAML indentation as ``sphum:`` in the above example.

UW YAML Keys
------------

``sphum:``
^^^^^^^^^^

The name of the tracer. The entry corresponds to the name chosen for the first line of the native ``field_table`` entry.

``longname:``
^^^^^^^^^^^^^

The descriptive name of the tracer.

``units:``
^^^^^^^^^^

The units for the tracer. This entry directly corresponds to the tracer units in the native ``field_table`` entry.

``profile_type:``
^^^^^^^^^^^^^^^^^

This block requires a ``name:`` entry that describes the profile type. Acceptable values (per the ``field_table`` spec) are ``fixed`` or ``profile``. The ``surface_value:`` is required in both cases, while the ``top_value:`` is required for only the ``profile`` option.
