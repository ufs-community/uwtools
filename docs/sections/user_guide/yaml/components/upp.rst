.. _upp_yaml:

upp
===

Structured YAML to run the UPP post-processor is validated by JSON Schema and requires the ``upp:`` block, described below. If UPP is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Here is a prototype UW YAML ``upp:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: ../../../../shared/upp.yaml

UW YAML for the ``upp:`` Block
------------------------------

execution:
^^^^^^^^^^

See :ref:`here <execution_yaml>` for details.

files_to_copy:
^^^^^^^^^^^^^^

TODO

files_to_link:
""""""""""""""

TODO

namelist_file:
""""""""""""""

TODO

run_dir:
^^^^^^^^

The path to the UPP run directory.
