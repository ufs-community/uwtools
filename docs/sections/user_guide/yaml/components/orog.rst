.. _orog_yaml:

orog
====

Structured YAML to run the component ``orog`` is validated by JSON Schema and requires the ``orog:`` block, described below. If ``orog`` is to be run via a batch system, the ``platform:`` block, described :ref:`here <platform_yaml>`, is also required.

Documentation for the UFS Utils ``orog`` program is :ufs-utils:`here <orog-gsl>`.

Here is a prototype UW YAML ``orog:`` block, explained in detail below:

.. highlight:: yaml
.. literalinclude:: /shared/orog.yaml

UW YAML for the ``orog:`` Block
-------------------------------

old_line1_items
^^^^^^^^^^^^^^^

Configuration parameters for the ``orog`` component corresponding to the first line entries prior to hash 57bd832 from (July 9, 2024). If using this section, a value for ``orog_file`` should also be provided.


execution:
^^^^^^^^^^

See :ref:`here <execution_yaml>` for details.

files_to_copy:
^^^^^^^^^^^^^^

See :ref:`this page <files_yaml>` for details.

files_to_link:
^^^^^^^^^^^^^^

Identical to ``files_to_copy:`` except that symbolic links will be created in the run directory instead of copies.

mask:
^^^^^

Boolean indicating whether only the land mask will be generated. Defaults to ".false."

merge:
^^^^^^

Path to an ocean merge file.

orog_file:
^^^^^^^^^^

Path to an output orography file if using a version of UFS_UTILS prior to hash 57bd832 from (July 9, 2024). If using this section, values for ``old_line1_items`` should also be provided.

rundir:
^^^^^^^

The path to the run directory.
