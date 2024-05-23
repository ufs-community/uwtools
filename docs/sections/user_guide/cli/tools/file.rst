``file``
========

The ``uw`` mode for handling filesystem files.

.. literalinclude:: file/help.cmd
   :emphasize-lines: 1
.. literalinclude:: file/help.out
   :language: text

.. _cli_file_copy_examples:

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

.. _cli_file_link_examples:

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
