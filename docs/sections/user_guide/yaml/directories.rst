.. _directories_yaml:

Directory Blocks
================

Directory blocks define a sequence of one or more directory to be created, nested under a ``mkdir:`` key. Each value is either an absolute path, or a path relative to the target directory.

Example block with aboslute paths:

.. code-block:: yaml

   mkdir:
     - /path/to/dir1
     - /path/to/dir2

Example block with relative paths:

.. code-block:: yaml

   mkdir:
     - /subdir/dir1
     - ../../dir2
