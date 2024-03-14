Mode ``file``
=============

The ``uw`` mode for handling filesystem files.

.. code-block:: text

   $ uw file --help
   usage: uw file [-h] ACTION ...
   
   Handle files
   
   Optional arguments:
     -h, --help
         Show help and exit
   
   Positional arguments:
     ACTION
       copy
         Copy files
       link
         Link files

.. _cli_file_copy_examples:

``copy``
--------

The ``copy`` action stages files in a target directory by copying files.

.. code-block:: text

   % uw file copy --help
   usage: uw file copy --target-dir PATH [-h] [--config-file PATH] [--dry-run] [--quiet] [--verbose]
                       [KEY ...]
   
   Copy files
   
   Required arguments:
     --target-dir PATH
         Path to target directory
   
   Optional arguments:
     -h, --help
         Show help and exit
     --config-file PATH, -c PATH
         Path to config file
     --dry-run
         Only log info, making no changes
     --quiet, -q
         Print no logging messages
     --verbose, -v
         Print all logging messages
     KEY
         YAML key leading to file dst/src block

Examples
^^^^^^^^


.. _cli_file_link_examples:

``link``
--------

The ``link`` action stages files in a target directory by linking files.

.. code-block:: text

   % uw file link --help
   usage: uw file link --target-dir PATH [-h] [--config-file PATH] [--dry-run] [--quiet] [--verbose]
                       [KEY ...]
   
   Link files
   
   Required arguments:
     --target-dir PATH
         Path to target directory
   
   Optional arguments:
     -h, --help
         Show help and exit
     --config-file PATH, -c PATH
         Path to config file
     --dry-run
         Only log info, making no changes
     --quiet, -q
         Print no logging messages
     --verbose, -v
         Print all logging messages
     KEY
         YAML key leading to file dst/src block

Examples
^^^^^^^^

