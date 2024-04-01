.. _mpas_init_yaml:

mpas_init
=========

Structured YAML to run the WRF preprocessing component ``mpas_init`` is validated by JSON Schema and requires the ``mpas_init:`` block, described below. If ``mpas_init`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Here is a prototype UW YAML ``mpas_init:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/mpas.yaml

When the ``init_atmosphere`` executable is built from the MPAS source code, static datainput files and default namelist and streams files are also created. Here we show an example of how an arbitrarily named ``user:`` section may be used to define helpful variables that are heavily reused through the rest of the configuration. In this example, the ``mpas_app`` entry is the path to where the MPAS model was installed.


UW YAML for the ``mpas:`` Block
-------------------------------

execution:
^^^^^^^^^^

See :ref:`here <execution_yaml>` for details.


boundary_conditions:
^^^^^^^^^^^^^^^^^^^^

Describes the boundary condition files needed for the forecast. These will most likely be the output
of the ``ungrib`` tool.

interval_hours:
"""""""""""""""

Frequency interval of the given files, in integer hours.

length:
"""""""

The length of the forecast in integer hours.

offset:
"""""""

How many hours earlier the external model used for boundary conditions started compared to the desired forecast cycle, in integer hours.

path:
"""""

An absolute path to the output of the ``ungrib`` tool that will be used to prepare MPAS-ready initial and lateral boundary conditions. The names of the files are specified in the ``streams.init_atmosphere`` XML file, and may be specified in the ``streams: values:`` block of the driver YAML.

files_to_copy:
^^^^^^^^^^^^^^

See :ref:`this page <files_yaml>` for details.

files_to_link:
^^^^^^^^^^^^^^

Identical to ``files_to_copy:`` except that symbolic links will be created in the run directory instead of copies.

run_dir:
^^^^^^^^

The path to the directory where ``mpas_init`` will find its namelist, streams file, and necessary data
files and write its outputs.

streams:
^^^^^^^^

path:
"""""

The path to the base ``streams.init_atmosphere`` file that comes from the MPAS build.

values:
"""""""

The set of key-value pairs that will render the appropriate XML entries in the streams input file.
