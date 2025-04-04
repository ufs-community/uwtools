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

Source paths prefixed with ``http://``, ``https://``, or ``hsi://`` will be copied from their upstream network locations to the local filesystem.

.. literalinclude:: fs/copy-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: fs/copy-help.out
   :language: text

Local-filesystem and HTTP Sources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Given a config containing a mapping from local-filesystem destination paths to source paths:

.. literalinclude:: fs/copy.yaml
   :language: yaml
.. literalinclude:: fs/copy.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy.out
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

.. literalinclude:: fs/copy.yaml
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

Use the ``!glob`` tag to specify that a local-filesystem source-path value should be treated as a glob pattern:

.. literalinclude:: fs/copy-glob.yaml
   :language: yaml
.. literalinclude:: fs/copy-glob.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-glob.out
   :language: text

The ``--report`` output can be especially useful in combination with glob patterns to allow downstream logic to process a set of copied files whose identity is not known in advance.

See :ref:`files_yaml_glob_support` for more examples and information on the semantics of the ``!glob`` tag.

HPSS Sources
^^^^^^^^^^^^

..
   NB: The .txt files below are not .cmd files and so will not be automatically executed to update
   their corresponding  static .out files. On a system with HPSS access, run 'make <outfile>' (using
   the name of an actual .out file) in the 'fs' directory to update after editing (or touch'ing) a
   .yaml or .txt file.

The examples in this section use the following files

.. literalinclude:: fs/copy-hpss-show-files.txt
   :language: text
.. literalinclude:: fs/copy-hpss-show-files.out
   :language: text

with this content:

.. literalinclude:: fs/copy-hpss-show-content.txt
   :language: text
.. literalinclude:: fs/copy-hpss-show-content.out
   :language: text

**HSI Support**

An ``hsi://`` URL can be used as a source path to copy full files from HPSS to the local filesystem:

.. literalinclude:: fs/copy-hpss-hsi-single.yaml
   :language: yaml
.. literalinclude:: fs/copy-hpss-hsi-single.txt
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-hpss-hsi-single.out
   :language: text

See :ref:`files_yaml_hsi_support` for more information on UW YAML support for ``hsi://`` sources.

Use the ``!glob`` tag to copy multiple full HPSS files:

.. literalinclude:: fs/copy-hpss-hsi-glob.yaml
   :language: yaml
.. literalinclude:: fs/copy-hpss-hsi-glob.txt
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-hpss-hsi-glob.out
   :language: text

See :ref:`files_yaml_hsi_glob_support` for more information on the use of the ``!glob`` tag in combination with ``hsi://`` sources.

**HTAR Support**

An ``htar://`` URL can be used as a source path to extract a member from an HPSS archive file and copy it to the local filesystem. The URL should include the path to the archive file and, as the URL `query string <https://en.wikipedia.org/wiki/Query_string>`_, the path to archive member to extract:

.. literalinclude:: fs/copy-hpss-htar-single.yaml
   :language: yaml
.. literalinclude:: fs/copy-hpss-htar-single.txt
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-hpss-htar-single.out
   :language: text

See :ref:`files_yaml_htar_support` for more information on UW YAML support for ``htar://`` sources.

Use the ``!glob`` tag to extract multiple members from one or more HPSS archive files:

.. literalinclude:: fs/copy-hpss-htar-glob.yaml
   :language: yaml
.. literalinclude:: fs/copy-hpss-htar-glob.txt
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/copy-hpss-htar-glob.out
   :language: text

See :ref:`files_yaml_htar_glob_support` for more information on the use of the ``!glob`` tag in combination with ``htar://`` sources.

``link``
--------

The ``link`` action stages items in a target directory by creating symbolic links to files, directories, or other symbolic links. It otherwise behaves similarly to ``copy`` (see above), but note the following:

* HTTP and HPSS sources are not supported.
* In addition to file, directories and other symbolic links can be linked.
* The ``link`` action links directories indentified by glob patterns, whereas the ``copy`` action ignores directories.
* Support for glob-pattern source values is the same as for ``link``.

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

.. literalinclude:: fs/makedirs.yaml
   :language: yaml
.. literalinclude:: fs/makedirs.cmd
   :language: text
   :emphasize-lines: 2
.. literalinclude:: fs/makedirs.out
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

.. literalinclude:: fs/makedirs.yaml
   :language: yaml
.. literalinclude:: fs/makedirs-no-target-dir-err.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: fs/makedirs-no-target-dir-err.out
   :language: text

The ``--report`` option behaves the same as for ``link`` (see above).
