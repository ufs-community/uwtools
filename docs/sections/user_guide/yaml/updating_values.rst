.. _updating_values:

Updating Values
===============

Some blocks support ``base_file:`` and ``update_values:`` entries. A ``base_file:`` entry specifies the path to a file to use as a basis for a particular runtime file. An ``update_values:`` entry specifies changes/additions to the base file. At least one of ``base_file:`` or ``update_values:`` must be provided. If only ``base_file:`` is provided, the file will be used as-is. If only ``update_values:`` is provided, it will completely define the runtime file in question. If both are provided, ``update_values:`` is used to modify the contents of ``base_file:``. The hierarchy of entries in the ``update_values:`` block must mirror that in the ``base_file:``. For example, a ``base_file:`` named ``people.yaml`` might contain:

.. code-block:: yaml

   person:
     age: 19
     address:
       city: Boston
       number: 12
       state: MA
       street: Acorn St
     name: Jane

A compatible YAML block updating the person's street address might then contain:

.. code-block:: yaml

   base_file: people.yaml
   update_values:
     person:
       address:
         street: Main St
         number: 99

The result would be:

.. code-block:: yaml

   person:
     age: 19
     address:
       city: Boston
       number: 99
       state: MA
       street: Main St
     name: Jane
