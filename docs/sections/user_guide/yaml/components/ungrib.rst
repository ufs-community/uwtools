.. _ungrib_yaml:

ungrib
======

Structured YAML to run the WRF preprocessing component ``ungrib`` (part of :wps:`WPS <>`) is validated by JSON Schema and requires the ``ungrib:`` block, described below. If ``ungrib`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

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

A list of paths to the GRIB-formatted files to be processed by ``ungrib``. 

rundir:
^^^^^^^

The path to the run directory.

start:
^^^^^^

The validtime of the initial element of ``gribfiles`` as an ISO8601 timestamp.

step:
^^^^^

The interval between successive elements of ``gribfiles`` as integer hours or as a string of the form ``hours[:minutes[:seconds]]``, where the ``hours``, ``minutes``, and ``seconds`` components are (possibly zero-padded) integers.

stop:
^^^^^

The validtime of the final element of ``gribfiles`` as an ISO8601 timestamp.

vtable:
^^^^^^^

The path to the correct variable table for the file to be processed by ``ungrib``.
