.. _defining_a_field_table:

Defining a ``field_table``
==========================

The :ufs-weather-model:`UFS Weather Model<>` requires as one of its inputs (:weather-model-io:`documented here<model-configuration-files>`) a ``field_table`` file in a :weather-model-io:`custom format<field-table-file>`. Its contents can be defined in a UW YAML, then created with ``uwtools``.

To generate a given ``field_table`` entry with the form:

.. code-block:: text

   "TRACER", "atmos_mod", "sphum"
             "longname",     "specific humidity"
             "units",        "kg/kg"
             "profile_type", "fixed", "surface_value=3.e-6" /

Entries can be represented in YAML with the form:

.. code-block:: text

   sphum:
     longname: specific humidity
     units: kg/kg
     profile_type:
       name: fixed
       surface_value: 3.e-6


Additional tracers may be added at the same level of YAML indentation as ``sphum:`` in the above example.

UW YAML Keys
------------

``sphum:``
^^^^^^^^^^

The short name of the tracer, to create the corresponding ``field_table`` entry's first line.

``longname:``
^^^^^^^^^^^^^

The descriptive name of the tracer.

``units:``
^^^^^^^^^^

The units for the tracer. This entry directly corresponds to the tracer units in the native ``field_table`` entry.

``profile_type:``
^^^^^^^^^^^^^^^^^

This block requires a ``name:`` entry that describes the profile type. Acceptable values (per the ``field_table`` spec) are ``fixed`` or ``profile``. The ``surface_value:`` is required in both cases, while the ``top_value:`` is required for only the ``profile`` option.
