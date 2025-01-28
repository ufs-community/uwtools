.. _ungrib_yaml:

ungrib
======

Structured YAML to run the WRF preprocessing component ``ungrib`` is validated by JSON Schema and requires the ``ungrib:`` block, described below. If ``ungrib`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

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

  **interval_hours:**

  Frequency interval of the given files, in integer hours.

  **max_leadtime:**

  The length of the forecast in integer hours.

  **offset:**

  How many hours earlier the external model used for boundary conditions started compared to the desired forecast cycle, in integer hours.

  **path:**

  An absolute-path template to the GRIB-formatted files to be processed by ``ungrib``. The Python ``int`` variables ``cycle_hour`` and ``forecast_hour`` will be interpolated into, e.g., ``/path/to/gfs.t{cycle_hour:02d}z.pgrb2.0p25.f{forecast_hour:03d}``. Note that this is a Python string template rather than a Jinja2 template.

rundir:
^^^^^^^

The path to the run directory.

vtable:
^^^^^^^

The path to the correct variable table for the file to be processed by ``ungrib``.
