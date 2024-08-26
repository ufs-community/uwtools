.. _files_yaml:

File Blocks
===========

File blocks define files to be staged in a target directory as copies or symbolic links. Keys in such blocks specify either absolute destination paths, or destination paths relative to the target directory. Values specify source paths.

Example block:

.. code-block:: yaml

   foo: /path/to/foo
   subdir/bar: /path/to/bar

* Result when copying:

.. code-block:: text

   target/
   ├── foo
   └── subdir
       └── bar

where ``foo`` and ``bar`` are copies of their respective source files.

* Result when linking:

.. code-block:: text

   target
   ├── foo -> /path/to/foo
   └── subdir
       └── bar -> /path/to/bar

where ``foo`` and ``bar`` are symbolic links.
