``fs``
======

.. _cli_fs_mode:

The ``uw`` mode for handling filesystem items (files and directories).

.. literalinclude:: fs/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: fs/help.out
   :language: text

``copy``
--------

The ``copy`` action stages files in a target directory by copying files. Any ``KEY`` positional arguments are used to navigate, in the order given, from the top of the config to the :ref:`file block <files_yaml>`.

Source paths prefixed with ``http://`` or ``https://`` will be copied from their upstream network locations to the local filesystem.

.. literalinclude:: fs/copy-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: fs/copy-help.out
   :language: text

Examples
^^^^^^^^

Given ``copy-config.yaml`` containing a mapping from local-filesystem destination paths to source paths

.. literalinclude:: fs/copy-basic-config.yaml
   :language: yaml
.. literalinclude:: fs/copy-basic-exec.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-basic-exec.out
   :language: text

Here, ``foo`` and ``bar`` are copies of their respective local-filesystem source files, and ``gpl`` is a copy of the upstream network source.

The ``--cycle`` and ``--leadtime`` options can be used to make Python ``datetime`` and ``timedelta`` objects, respectively, available for use in Jinja2 expression in the config. For example:

.. literalinclude:: fs/copy-timedep-config.yaml
   :language: yaml
.. literalinclude:: fs/copy-timedep-exec.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-timedep-exec.out
   :language: text

The ``--target-dir`` option need not be specified when all destination paths are absolute, and will never be applied to absolute destination paths. If any destination paths are relative, however, it is an error not to provide a target directory:

.. literalinclude:: fs/copy-basic-config.yaml
   :language: yaml
.. literalinclude:: fs/copy-no-target-dir-err-exec.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: fs/copy-no-target-dir-err-exec.out
   :language: text

When the ``--report`` option is specified, a report of files not copied ("not-ready") and copied ("ready") will be printed to ``stdout`` as machine-readable JSON. For example, using a config specifying both available and unavailable source files:

.. literalinclude:: fs/copy-report-config.yaml
   :language: yaml
.. literalinclude:: fs/copy-report-exec.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-report-exec.out
   :language: text

Since ``uwtools`` logs to ``stderr``, log and report output can be separated and the latter processed with a tool like ``jq``:

.. literalinclude:: fs/copy-report-jq-exec.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-report-jq-exec.out
   :language: text

Use the ``!glob`` tag to specify that a source-path value should be treated as a glob pattern:

.. literalinclude:: fs/copy-glob-config.yaml
   :language: yaml
.. literalinclude:: fs/copy-glob-exec.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-glob-exec.out
   :language: text

See :ref:`files_yaml` for more information on the semantics of the `!glob` tag and wildcard copies. Note that directories are excluded, and recursion (deep copies) are not supported.

``link``
--------

The ``link`` action stages items in a target directory by creating symbolic links to files, directories, or other symbolic links. It otherwise behaves similarly to ``copy`` (see above), but note the following:

* In addition to file, directories and other symbolic links can be linked.
* HTTP(S) sources are not supported.
* Support for wildcard source values is the same as for ``link``.

.. literalinclude:: fs/link-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: fs/link-help.out
   :language: text

``makedirs``
------------

The ``makedirs`` action creates directories. Any ``KEY`` positional arguments are used to navigate, in the order given, from the top of the config to the :ref:`makedirs block <makedirs_yaml>`, which must nest under a ``makedirs:`` key.

.. literalinclude:: fs/makedirs-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: fs/makedirs-help.out
   :language: text

Examples
^^^^^^^^

Given ``makedirs-config.yaml`` containing

.. literalinclude:: fs/makedirs-basic-config.yaml
   :language: yaml
.. literalinclude:: fs/makedirs-basic-exec.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/makedirs-basic-exec.out
   :language: text

The ``--cycle`` and ``--leadtime`` options can be used to make Python ``datetime`` and ``timedelta`` objects, respectively, available for use in Jinja2 expression in the config. For example:

.. literalinclude:: fs/makedirs-timedep-config.yaml
   :language: yaml
.. literalinclude:: fs/makedirs-timedep-exec.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/makedirs-timedep-exec.out
   :language: text

The ``--target-dir`` option need not be specified when all directory paths are absolute, and will never be applied to absolute paths. If any paths are relative, however, it is an error not to provide a target directory:

.. literalinclude:: fs/makedirs-basic-config.yaml
   :language: yaml
.. literalinclude:: fs/makedirs-no-target-dir-err-exec.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: fs/makedirs-no-target-dir-err-exec.out
   :language: text

The ``--report`` option behaves the same as for ``link`` (see above).
