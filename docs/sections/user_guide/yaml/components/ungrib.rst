.. _ungrib_yaml:

ungrib
======

Structured YAML to run the WRF preprocessing component ``ungrib`` (:wps:`documentation <program-ungrib>`) is validated by JSON Schema and requires the ``ungrib:`` block, described below. If ``ungrib`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

.. include:: /shared/injected_cycle.rst

Here is a prototype UW YAML ``ungrib:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/ungrib.yaml

UW YAML for the ``ungrib:`` Block
---------------------------------

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

gribfiles:
^^^^^^^^^^

Describes the GRIB-formatted files to be processed by ``ungrib``.

  **files:**

  A list of absolute paths to the GRIB-formatted files to be processed by ``ungrib``. 

  **interval_hours:**

  Frequency interval of the given files, in integer hours.

  **max_leadtime:**

  The maximum forecast leadtime to process. This may be the same as the forecast length, or a lower leadtime.

rundir:
^^^^^^^

The path to the run directory.

vtable:
^^^^^^^

The path to the correct variable table for the file to be processed by ``ungrib``.
