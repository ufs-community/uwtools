``file``
========

.. _cli_file_mode:

The ``uw`` mode for handling filesystem files.

.. literalinclude:: file/help.cmd
   :emphasize-lines: 1
.. literalinclude:: file/help.out
   :language: text

``copy``
--------

The ``copy`` action stages files in a target directory by copying files. Any ``KEY`` positional arguments are used to navigate, in the order given, from the top of the config to the :ref:`file block <files_yaml>`.

.. literalinclude:: file/copy-help.cmd
   :emphasize-lines: 1
.. literalinclude:: file/copy-help.out
   :language: text

Examples
^^^^^^^^

Given ``copy-config.yaml`` containing

.. literalinclude:: file/copy-config.yaml
   :language: yaml
.. literalinclude:: file/copy-exec.cmd
   :emphasize-lines: 2
.. literalinclude:: file/copy-exec.out
   :language: text

Here, ``foo`` and ``bar`` are copies of their respective source files.

The ``--cycle`` and ``--leadtime`` options can be used to make Python ``datetime`` and ``timedelta`` objects, respectively, available for use in Jinja2 expression in the config. For example:

.. literalinclude:: file/copy-config-timedep.yaml
   :language: yaml
.. literalinclude:: file/copy-exec-timedep.cmd
   :emphasize-lines: 2
.. literalinclude:: file/copy-exec-timedep.out
   :language: text

The ``--target-dir`` option is optional when all destination paths are absolute, and will never be applied to absolute destination paths. If any destination paths are relative, however, it is an error not to provide a target directory:

.. literalinclude:: file/copy-config.yaml
   :language: yaml
.. literalinclude:: file/copy-exec-no-target-dir-err.cmd
   :emphasize-lines: 1
.. literalinclude:: file/copy-exec-no-target-dir-err.out
   :language: text

``link``
--------

The ``link`` action stages files in a target directory by linking files, directories, or other symbolic links. Any ``KEY`` positional arguments are used to navigate, in the order given, from the top of the config to the :ref:`file block <files_yaml>`.

.. literalinclude:: file/link-help.cmd
   :emphasize-lines: 1
.. literalinclude:: file/link-help.out
   :language: text

Examples
^^^^^^^^

Given ``link-config.yaml`` containing

.. literalinclude:: file/link-config.yaml
   :language: yaml
.. literalinclude:: file/link-exec.cmd
   :emphasize-lines: 2
.. literalinclude:: file/link-exec.out
   :language: text

Here, ``foo`` and ``bar`` are symbolic links.

The ``--cycle`` and ``--leadtime`` options can be used to make Python ``datetime`` and ``timedelta`` objects, respectively, available for use in Jinja2 expression in the config. For example:

.. literalinclude:: file/link-config-timedep.yaml
   :language: yaml
.. literalinclude:: file/link-exec-timedep.cmd
   :emphasize-lines: 2
.. literalinclude:: file/link-exec-timedep.out
   :language: text

The ``--target-dir`` option is optional when all linkname paths are absolute, and will never be applied to absolute linkname paths. If any linkname paths are relative, however, it is an error not to provide a target directory:

.. literalinclude:: file/link-config.yaml
   :language: yaml
.. literalinclude:: file/link-exec-no-target-dir-err.cmd
   :emphasize-lines: 1
.. literalinclude:: file/link-exec-no-target-dir-err.out
   :language: text

``mkdir``
---------

The ``mkdir`` action creates directories. Any ``KEY`` positional arguments are used to navigate, in the order given, from the top of the config to the :ref:`mkdir block <mkdir_yaml>`.

.. literalinclude:: file/mkdir-help.cmd
   :emphasize-lines: 1
.. literalinclude:: file/mkdir-help.out
   :language: text

Examples
^^^^^^^^

Given ``mkdir-config.yaml`` containing

.. literalinclude:: file/mkdir-config.yaml
   :language: yaml
.. literalinclude:: file/mkdir-exec.cmd
   :emphasize-lines: 2
.. literalinclude:: file/mkdir-exec.out
   :language: text

The ``--cycle`` and ``--leadtime`` options can be used to make Python ``datetime`` and ``timedelta`` objects, respectively, available for use in Jinja2 expression in the config. For example:

.. literalinclude:: file/mkdir-config-timedep.yaml
   :language: yaml
.. literalinclude:: file/mkdir-exec-timedep.cmd
   :emphasize-lines: 2
.. literalinclude:: file/mkdir-exec-timedep.out
   :language: text

The ``--target-dir`` option is optional when all directory paths are absolute, and will never be applied to absolute paths. If any paths are relative, however, it is an error not to provide a target directory:

.. literalinclude:: file/mkdir-config.yaml
   :language: yaml
.. literalinclude:: file/mkdir-exec-no-target-dir-err.cmd
   :emphasize-lines: 1
.. literalinclude:: file/mkdir-exec-no-target-dir-err.out
   :language: text
