``file``
========

The ``uw`` mode for handling filesystem files.

.. code-block:: text

   $ uw file --help
   usage: uw file [-h] [--version] ACTION ...

   Handle files

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit

   Positional arguments:
     ACTION
       copy
         Copy files
       link
         Link files

.. _cli_file_copy_examples:

``copy``
--------

The ``copy`` action stages files in a target directory by copying files. Any ``KEY`` positional arguments are used to navigate, in the order given, from the top of the config to the :ref:`file block <files_yaml>`.

.. code-block:: text

   $ uw file copy --help
   usage: uw file copy --target-dir PATH [-h] [--version] [--config-file PATH] [--dry-run] [--quiet]
                       [--verbose]
                       [KEY ...]

   Copy files

   Required arguments:
     --target-dir PATH
         Path to target directory

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit
     --config-file PATH, -c PATH
         Path to UW YAML config file
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

Given ``config.yaml`` containing

.. code-block:: yaml

   config:
     files:
       foo: /path/to/foo
       subdir/bar: /path/to/bar

.. code-block:: text

   $ uw file copy --target-dir /tmp/target --config-file config.yaml config files
   [2024-03-14T19:00:02]     INFO Validating config against internal schema files-to-stage
   [2024-03-14T19:00:02]     INFO 0 UW schema-validation errors found
   [2024-03-14T19:00:02]     INFO File copies: Initial state: Pending
   [2024-03-14T19:00:02]     INFO File copies: Checking requirements
   [2024-03-14T19:00:02]     INFO Copy /tmp/source/foo -> /tmp/target/foo: Initial state: Pending
   [2024-03-14T19:00:02]     INFO Copy /tmp/source/foo -> /tmp/target/foo: Checking requirements
   [2024-03-14T19:00:02]     INFO Copy /tmp/source/foo -> /tmp/target/foo: Requirement(s) ready
   [2024-03-14T19:00:02]     INFO Copy /tmp/source/foo -> /tmp/target/foo: Executing
   [2024-03-14T19:00:02]     INFO Copy /tmp/source/foo -> /tmp/target/foo: Final state: Ready
   [2024-03-14T19:00:02]     INFO Copy /tmp/source/bar -> /tmp/target/subdir/bar: Initial state: Pending
   [2024-03-14T19:00:02]     INFO Copy /tmp/source/bar -> /tmp/target/subdir/bar: Checking requirements
   [2024-03-14T19:00:02]     INFO Copy /tmp/source/bar -> /tmp/target/subdir/bar: Requirement(s) ready
   [2024-03-14T19:00:02]     INFO Copy /tmp/source/bar -> /tmp/target/subdir/bar: Executing
   [2024-03-14T19:00:02]     INFO Copy /tmp/source/bar -> /tmp/target/subdir/bar: Final state: Ready
   [2024-03-14T19:00:02]     INFO File copies: Final state: Ready

After executing this command:

.. code-block:: text

   $ tree /tmp/target
   /tmp/target
   ├── foo
   └── subdir
       └── bar

Here, ``foo`` and ``bar`` are copies of their respective source files.

.. _cli_file_link_examples:

``link``
--------

The ``link`` action stages files in a target directory by linking files, directories, or other symbolic links. Any ``KEY`` positional arguments are used to navigate, in the order given, from the top of the config to the :ref:`file block <files_yaml>`.

.. code-block:: text

   $ uw file link --help
   usage: uw file link --target-dir PATH [-h] [--version] [--config-file PATH] [--dry-run] [--quiet]
                       [--verbose]
                       [KEY ...]

   Link files

   Required arguments:
     --target-dir PATH
         Path to target directory

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit
     --config-file PATH, -c PATH
         Path to UW YAML config file
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

Given ``config.yaml`` containing

.. code-block:: yaml

   config:
     files:
       foo: /path/to/foo
       subdir/bar: /path/to/bar

.. code-block:: text

   $ uw file link --target-dir /tmp/target --config-file config.yaml config files
   [2024-03-14T19:02:49]     INFO Validating config against internal schema files-to-stage
   [2024-03-14T19:02:49]     INFO 0 UW schema-validation errors found
   [2024-03-14T19:02:49]     INFO File links: Initial state: Pending
   [2024-03-14T19:02:49]     INFO File links: Checking requirements
   [2024-03-14T19:02:49]     INFO Link /tmp/target/foo -> /tmp/source/foo: Initial state: Pending
   [2024-03-14T19:02:49]     INFO Link /tmp/target/foo -> /tmp/source/foo: Checking requirements
   [2024-03-14T19:02:49]     INFO Link /tmp/target/foo -> /tmp/source/foo: Requirement(s) ready
   [2024-03-14T19:02:49]     INFO Link /tmp/target/foo -> /tmp/source/foo: Executing
   [2024-03-14T19:02:49]     INFO Link /tmp/target/foo -> /tmp/source/foo: Final state: Ready
   [2024-03-14T19:02:49]     INFO Link /tmp/target/subdir/bar -> /tmp/source/bar: Initial state: Pending
   [2024-03-14T19:02:49]     INFO Link /tmp/target/subdir/bar -> /tmp/source/bar: Checking requirements
   [2024-03-14T19:02:49]     INFO Link /tmp/target/subdir/bar -> /tmp/source/bar: Requirement(s) ready
   [2024-03-14T19:02:49]     INFO Link /tmp/target/subdir/bar -> /tmp/source/bar: Executing
   [2024-03-14T19:02:49]     INFO Link /tmp/target/subdir/bar -> /tmp/source/bar: Final state: Ready
   [2024-03-14T19:02:49]     INFO File links: Final state: Ready

After executing this command:

.. code-block:: text

   $ tree /tmp/target
   /tmp/target
   ├── foo -> /tmp/source/foo
   └── subdir
       └── bar -> /tmp/source/bar

Here, ``foo`` and ``bar`` are symbolic links.
