``fs``
======

.. _cli_fs_mode:

The ``uw`` mode for handling filesystem items (files and directories).

.. literalinclude:: fs/help.cmd
   :emphasize-lines: 1
.. literalinclude:: fs/help.out
   :language: text

``copy``
--------

The ``copy`` action stages files in a target directory by copying files. Any ``KEY`` positional arguments are used to navigate, in the order given, from the top of the config to the :ref:`file block <files_yaml>`.

.. literalinclude:: fs/copy-help.cmd
   :emphasize-lines: 1
.. literalinclude:: fs/copy-help.out
   :language: text

Examples
^^^^^^^^

Given ``copy-config.yaml`` containing

.. literalinclude:: fs/copy-config.yaml
   :language: yaml
.. literalinclude:: fs/copy-exec.cmd
   :emphasize-lines: 2
.. literalinclude:: fs/copy-exec.out
   :language: text

Here, ``foo`` and ``bar`` are copies of their respective source files.

The ``--cycle`` and ``--leadtime`` options can be used to make Python ``datetime`` and ``timedelta`` objects, respectively, available for use in Jinja2 expression in the config. For example:

.. literalinclude:: fs/copy-config-timedep.yaml
   :language: yaml
.. literalinclude:: fs/copy-exec-timedep.cmd
   :emphasize-lines: 2
.. literalinclude:: fs/copy-exec-timedep.out
   :language: text

The ``--target-dir`` option is optional when all destination paths are absolute, and will never be applied to absolute destination paths. If any destination paths are relative, however, it is an error not to provide a target directory:

.. literalinclude:: fs/copy-config.yaml
   :language: yaml
.. literalinclude:: fs/copy-exec-no-target-dir-err.cmd
   :emphasize-lines: 1
.. literalinclude:: fs/copy-exec-no-target-dir-err.out
   :language: text

``link``
--------

The ``link`` action stages files in a target directory by linking files, directories, or other symbolic links. Any ``KEY`` positional arguments are used to navigate, in the order given, from the top of the config to the :ref:`file block <files_yaml>`.

.. literalinclude:: fs/link-help.cmd
   :emphasize-lines: 1
.. literalinclude:: fs/link-help.out
   :language: text

Examples
^^^^^^^^

Given ``link-config.yaml`` containing

.. literalinclude:: fs/link-config.yaml
   :language: yaml
.. literalinclude:: fs/link-exec.cmd
   :emphasize-lines: 2
.. literalinclude:: fs/link-exec.out
   :language: text

Here, ``foo`` and ``bar`` are symbolic links.

The ``--cycle`` and ``--leadtime`` options can be used to make Python ``datetime`` and ``timedelta`` objects, respectively, available for use in Jinja2 expression in the config. For example:

.. literalinclude:: fs/link-config-timedep.yaml
   :language: yaml
.. literalinclude:: fs/link-exec-timedep.cmd
   :emphasize-lines: 2
.. literalinclude:: fs/link-exec-timedep.out
   :language: text

The ``--target-dir`` option is optional when all linkname paths are absolute, and will never be applied to absolute linkname paths. If any linkname paths are relative, however, it is an error not to provide a target directory:

.. literalinclude:: fs/link-config.yaml
   :language: yaml
.. literalinclude:: fs/link-exec-no-target-dir-err.cmd
   :emphasize-lines: 1
.. literalinclude:: fs/link-exec-no-target-dir-err.out
   :language: text

``makedirs``
------------

The ``makedirs`` action creates directories. Any ``KEY`` positional arguments are used to navigate, in the order given, from the top of the config to the :ref:`makedirs block <makedirs_yaml>`.

.. literalinclude:: fs/makedirs-help.cmd
   :emphasize-lines: 1
.. literalinclude:: fs/makedirs-help.out
   :language: text

Examples
^^^^^^^^

Given ``makedirs-config.yaml`` containing

.. literalinclude:: fs/makedirs-config.yaml
   :language: yaml
.. literalinclude:: fs/makedirs-exec.cmd
   :emphasize-lines: 2
.. literalinclude:: fs/makedirs-exec.out
   :language: text

The ``--cycle`` and ``--leadtime`` options can be used to make Python ``datetime`` and ``timedelta`` objects, respectively, available for use in Jinja2 expression in the config. For example:

.. literalinclude:: fs/makedirs-config-timedep.yaml
   :language: yaml
.. literalinclude:: fs/makedirs-exec-timedep.cmd
   :emphasize-lines: 2
.. literalinclude:: fs/makedirs-exec-timedep.out
   :language: text

The ``--target-dir`` option is optional when all directory paths are absolute, and will never be applied to absolute paths. If any paths are relative, however, it is an error not to provide a target directory:

.. literalinclude:: fs/makedirs-config.yaml
   :language: yaml
.. literalinclude:: fs/makedirs-exec-no-target-dir-err.cmd
   :emphasize-lines: 1
.. literalinclude:: fs/makedirs-exec-no-target-dir-err.out
   :language: text
