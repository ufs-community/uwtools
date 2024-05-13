.. _mpas_yaml:

mpas
====

Structured YAML to run MPAS is validated by JSON Schema and requires the ``mpas:`` block, described below. If ``mpas`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

.. include:: ../../../../shared/injected_cycle.rst

Here is a prototype UW YAML ``mpas:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/mpas.yaml

An MPAS build provides prototype versions of certain required runtime files. Here, an arbitrarily named ``user:`` block defines an ``mpas_app`` variable, pointing to the directory where MPAS was installed, to reduce duplication in references to those files.

UW YAML for the ``mpas:`` Block
-------------------------------

execution:
^^^^^^^^^^

See :ref:`this page <execution_yaml>` for details.

boundary_conditions:
^^^^^^^^^^^^^^^^^^^^

Describes the boundary condition files needed for the forecast. These will be the output from the ``init_atmosphere`` executable, which may be run using the ``mpas_init`` UW driver. Please see its documentation :ref:`here <mpas_init_yaml>`.

  **interval_hours:**

  Frequency interval of the given files, in integer hours.

  **offset:**

  How many hours earlier the external model used for boundary conditions started compared to the desired forecast cycle, in integer hours.

  **path:**

An absolute path to the MPAS-ready files to be used for initial and lateral boundary conditions input. The names of the files are specified in the MPAS ``streams.atmosphere`` XML file, and may be specified in the ``streams: values:`` block of the driver YAML.

length:
^^^^^^^

The length of the forecast in integer hours.

files_to_copy:
^^^^^^^^^^^^^^

See :ref:`this page <files_yaml>` for details.

To reduce duplication of information in this section, it may be helpful to template the file that depends on the number of cores being used to run the executable. For example, instead of:

.. code-block:: text

   mpas:
     files_to_copy:
       conus.graph.info.part.32: /path/to/conus.graph.info.part.32

Jinja2 expressions can be used to reference the number of cores used in execution:

.. code-block:: text

   mpas:
     files_to_copy:
       conus.graph.info.part.{{mpas.execution["batchargs"]["cores"]}}: /path/to/conus.graph.info.part.{{mpas.execution["batchargs"]["cores"]}}

files_to_link:
^^^^^^^^^^^^^^

Identical to ``files_to_copy:`` except that symbolic links will be created in the run directory instead of copies.

run_dir:
^^^^^^^^

The path to the run directory.

streams:
^^^^^^^^

  **path:**

  The path to the base ``streams.atmosphere`` file that comes from the MPAS build.

  **values:**

  The set of key-value pairs that will render the appropriate XML entries in the streams input file.
