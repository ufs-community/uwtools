.. _mpas_init_yaml:

mpas_init
=========

Structured YAML to run MPAS Init is validated by JSON Schema and requires the ``mpas_init:`` block, described below. If ``mpas_init`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

.. include:: /shared/injected_cycle.rst

Here is a prototype UW YAML ``mpas_init:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/drivers/mpas_init.yaml

An MPAS build provides prototype versions of certain required runtime files. Here, an arbitrarily named ``user:`` block defines an ``mpas_app`` variable, pointing to the directory where MPAS was installed, to reduce duplication in references to those files.

UW YAML for the ``mpas_init:`` Block
------------------------------------

boundary_conditions:
^^^^^^^^^^^^^^^^^^^^

Describes the boundary condition files needed for the forecast. These will most likely be the output of the ``ungrib`` tool.

  **interval_hours:**

  Frequency interval of the given files, in integer hours.

  **length:**

  The length of the forecast in integer hours.

  **offset:**

  How many hours earlier the external model used for boundary conditions started compared to the desired forecast cycle, in integer hours.

  **path:**

An absolute path to the output of the ``ungrib`` tool that will be used to prepare MPAS-ready initial and lateral boundary conditions. The names of the files are specified in the ``streams.init_atmosphere`` XML file, and may be specified in the ``streams: values:`` block of the driver YAML.

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

.. include:: /shared/stager.rst

To reduce duplication of information in these sections, it may be helpful to template the file that depends on the number of cores being used to run the executable. For example, instead of:

.. code-block:: text

   mpas_init:
     files_to_copy:
       conus.graph.info.part.4: /path/to/conus.graph.info.part.4

Jinja2 expressions can be used to reference the number of cores used in execution:

.. code-block:: text

   mpas_init:
     files_to_copy:
       conus.graph.info.part.{{mpas_init.execution["batchargs"]["cores"]}}: /path/to/conus.graph.info.part.{{mpas_init.execution["batchargs"]["cores"]}}

namelist:
^^^^^^^^^

Supports ``base_file:`` and ``update_values:`` blocks (see :ref:`updating_values` for details).

.. include:: /shared/validate_namelist.rst

rundir:
^^^^^^^

The path to the run directory.

.. include:: /shared/mpas_streams.rst
