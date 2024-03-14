.. _files_yaml:

File Blocks:
============

File blocks define files to be staged in a target directory as copies or symbolic links. Keys in such blocks specify destination paths relative to the target directory, and values specify source paths.

Example block:

.. code-block:: yaml

   foo: /path/to/foo
   subdir/bar: /path/to/bar

For a copy action, this block would lead to

.. code-block:: text

   target/
   ├── foo
   └── subdir
       └── bar

For a link action, this block would lead to

.. code-block:: text

   target
   ├── foo -> /path/to/foo
   └── subdir
       └── bar -> /path/to/bar
