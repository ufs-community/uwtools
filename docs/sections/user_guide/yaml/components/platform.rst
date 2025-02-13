.. _platform_yaml:

The ``platform:`` Block
=======================

The top-level UW YAML ``platform:`` block, referenced by multiple component drivers, is described below. It is validated by JSON Schema.

Example block:

.. code-block:: yaml

   platform:
    account: acctnname
    scheduler: slurm

account:
^^^^^^^^

The account name to use when requesting resources from the batch job scheduler.

scheduler:
^^^^^^^^^^

One of ``lsf``, ``pbs``, or ``slurm``.
