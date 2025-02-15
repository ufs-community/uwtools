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

Given a config containing a mapping from local-filesystem destination paths to source paths

.. literalinclude:: fs/copy-basic.yaml
   :language: yaml
.. literalinclude:: fs/copy-basic.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-basic.out
   :language: text

Here, ``foo`` and ``bar`` are copies of their respective local-filesystem source files, and ``gpl`` is a copy of the upstream network source.

The ``--cycle`` and ``--leadtime`` options can be used to make Python ``datetime`` and ``timedelta`` objects, respectively, available for use in Jinja2 expression in the config. For example:

.. literalinclude:: fs/copy-timedep.yaml
   :language: yaml
.. literalinclude:: fs/copy-timedep.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-timedep.out
   :language: text

The ``--target-dir`` option need not be specified when all destination paths are absolute, and will never be applied to absolute destination paths. If any destination paths are relative, however, it is an error not to provide a target directory:

.. literalinclude:: fs/copy-basic.yaml
   :language: yaml
.. literalinclude:: fs/copy-no-target-dir-err.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: fs/copy-no-target-dir-err.out
   :language: text

When the ``--report`` option is specified, a report of files not copied ("not-ready") and copied ("ready") will be printed to ``stdout`` as machine-readable JSON. For example, using a config specifying both available and unavailable source files:

.. literalinclude:: fs/copy-report.yaml
   :language: yaml
.. literalinclude:: fs/copy-report.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-report.out
   :language: text

Since ``uwtools`` logs to ``stderr``, log and report output can be separated and the latter processed with a tool like ``jq``:

.. literalinclude:: fs/copy-report-jq.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-report-jq.out
   :language: text

Use the ``!glob`` tag to specify that a source-path value should be treated as a glob pattern:

.. literalinclude:: fs/copy-glob.yaml
   :language: yaml
.. literalinclude:: fs/copy-glob.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-glob.out
   :language: text

The ``--report`` output can be especially useful in combination with wildcards to allow downstream logic to process a set of copied files whose identity is not known in advance.

Note that directories are excluded, and recursive copies are not supported. To recursively copy from a shell script, where you might otherwise use ``uw fs copy``, consider using ``cp -r``; and from Python code where you might otherwise call ``uwtools.api.fs.copy()``, consider using the standard-library `shutil.copytree()` <https://docs.python.org/3/library/shutil.html#shutil.copytree>`_. For more control, including file-grained include and exclude, consider the unrivaled `rsync` <https://rsync.samba.org/>`_, which can be installed from conda in case your system does not already provide it. It can be called from shell scripts, or via `subprocess` <https://docs.python.org/3/library/subprocess.html>`_ from Python.

See :ref:`files_yaml` for more information on the semantics of the `!glob` tag and wildcard copies.

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

Given a config containing

.. literalinclude:: fs/makedirs-basic.yaml
   :language: yaml
.. literalinclude:: fs/makedirs-basic.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/makedirs-basic.out
   :language: text

The ``--cycle`` and ``--leadtime`` options can be used to make Python ``datetime`` and ``timedelta`` objects, respectively, available for use in Jinja2 expression in the config. For example:

.. literalinclude:: fs/makedirs-timedep.yaml
   :language: yaml
.. literalinclude:: fs/makedirs-timedep.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/makedirs-timedep.out
   :language: text

The ``--target-dir`` option need not be specified when all directory paths are absolute, and will never be applied to absolute paths. If any paths are relative, however, it is an error not to provide a target directory:

.. literalinclude:: fs/makedirs-basic.yaml
   :language: yaml
.. literalinclude:: fs/makedirs-no-target-dir-err.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: fs/makedirs-no-target-dir-err.out
   :language: text

The ``--report`` option behaves the same as for ``link`` (see above).
