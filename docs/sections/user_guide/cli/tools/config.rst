``config``
==========

The ``uw`` mode for handling configuration files (configs).

.. literalinclude:: config/help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: config/help.out
   :language: text

.. _cli_config_compare_examples:

``compare``
-----------

The ``compare`` action compares two config files.

.. literalinclude:: config/compare-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: config/compare-help.out
   :language: text

Examples
^^^^^^^^

The examples that follow use identical namelist files ``a.nml`` and ``b.nml`` with contents:

.. literalinclude:: config/a.nml
   :language: fortran

* To compare two config files with the same contents:

  .. literalinclude:: config/compare-match.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/compare-match.out
     :language: text

* If there are differences between the config files, they will be shown below the dashed line. For example, ``c.nml`` is missing the line ``recipient: World``:

  .. literalinclude:: config/c.nml
     :language: fortran
  .. literalinclude:: config/compare-diff.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/compare-diff.out
     :language: text

* If a config file has an unrecognized (or no) extension, ``uw`` will not know how to parse its contents:

  .. literalinclude:: config/compare-bad-extension.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/compare-bad-extension.out
     :language: text

  The format must be explicitly specified (``a.txt`` is a copy of ``a.nml``):

  .. literalinclude:: config/compare-bad-extension-fix.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/compare-bad-extension-fix.out
     :language: text

* To request verbose log output:

  .. literalinclude:: config/compare-verbose.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/compare-verbose.out
     :language: text

  Note that ``uw`` logs to ``stderr``. Use :shell-redirection:`shell redirection<>` as needed.

.. note:: Comparisons are supported only for configs of the same format, e.g. YAML vs YAML, Fortran namelist vs Fortran namelist, etc. ``uw`` will flag invalid comparisons:

  .. literalinclude:: config/compare-format-mismatch.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/compare-format-mismatch.out
     :language: text

.. _cli_config_realize_examples:

``realize``
-----------

In ``uw`` terminology, to realize a configuration file is to transform it from its raw form into its final, usable state. The ``realize`` action can build a complete config file from two or more separate files.

.. literalinclude:: config/realize-help.cmd
   :emphasize-lines: 1
.. literalinclude:: config/realize-help.out
   :language: text

Examples
^^^^^^^^

The initial examples in this section use YAML file ``config.yaml`` with contents:

.. literalinclude:: config/config.yaml
   :language: yaml

and YAML file ``update.yaml`` with contents:

.. literalinclude:: config/update.yaml
   :language: yaml

* For a report of input-config values with unrendered Jinja2 variables/expressions or empty/null keys:

  .. literalinclude:: config/realize-values-needed.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-values-needed.out
     :language: text

* To realize the config to ``stdout``, the output format must be explicitly specified:

  .. literalinclude:: config/realize-stdout.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-stdout.out
     :language: text

  :shell-redirection:`Shell redirection<>` may also be used to stream output to a file, another process, etc.

* Values in the input file can be updated via an optional update file:

  .. literalinclude:: config/realize-update-file.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-update-file.out
     :language: text

* To realize the config to a file via command-line argument:

  .. literalinclude:: config/realize-update-file-outfile.cmd
     :language: text
     :emphasize-lines: 2
  .. literalinclude:: config/realize-update-file-outfile.out
     :language: text

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. literalinclude:: config/realize-dry-run.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-dry-run.out
     :language: text

* If the config file has an unrecognized (or no) extension, ``uw`` will not automatically know how to parse its contents:

  .. literalinclude:: config/realize-extension-file-bad.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-extension-file-bad.out
     :language: text

  The format must be explicitly specified  (here, ``config.txt`` is a copy of ``config.yaml``):

  .. literalinclude:: config/realize-extension-file-fix.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-extension-file-fix.out
     :language: text

* Similarly, if an input file is read from ``stdin``, ``uw`` will not automatically know how to parse its contents:

  .. literalinclude:: config/realize-extension-stdin-bad.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-extension-stdin-bad.out
     :language: text

  The format must be explicitly specified:

  .. literalinclude:: config/realize-extension-stdin-fix.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-extension-stdin-fix.out
     :language: text

* This example demonstrates: 1. Reading a config from ``stdin``, 2. Extracting a specific subsection with the ``--key-path`` option, and 3. Writing the output in a different format:

  .. literalinclude:: config/realize-combo.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-combo.out
     :language: text

.. note:: Combining configs with incompatible depths is not supported. ``ini`` configs are depth-2, as they organize their key-value pairs (one level) under top-level sections or namelists (a second level). ``sh`` configs are depth-1, and ``yaml`` configs have arbitrary depth.

   For example, when attempting to generate a ``sh`` config from the original depth-2 ``config.yaml``:

   .. literalinclude:: config/realize-depth-mismatch.cmd
      :language: text
      :emphasize-lines: 1
   .. literalinclude:: config/realize-depth-mismatch.out
      :language: text

   ``nml`` configs are technically depth-2, but in order to support specification of Fortran derived type (aka user-defined type) members, a mapping between arbitrary-depth YAML and Fortran namelist is supported. For example, ``derived-type.yaml`` with contents

   .. literalinclude:: config/derived-type.yaml
     :language: yaml

   would be rendered as a Fortran namelist like this:

   .. literalinclude:: config/realize-nml-derived-type.cmd
      :language: text
      :emphasize-lines: 1
   .. literalinclude:: config/realize-nml-derived-type.out
      :language: text

   Fortran array-item/slice syntax (e.g. ``a(1) = 11``, ``a(2,3) = 22, 33``, etc.) is not currently supported.

* It is possible to provide the update config, rather than the input config, on ``stdin``. Usage rules are as follows:

  * Only if either ``--update-file`` or ``--update-config`` are specified will ``uw`` attempt to read and apply update values to the input config.
  * If ``--update-file`` is provided with an unrecognized (or no) extension, or if the update values are provided on ``stdin``, ``--update-format`` must be used to specify the correct format.
  * When updating, the input config, the update config, or both must be provided via file; they cannot be streamed from ``stdin`` simultaneously.

  For example, here the update config is provided on ``stdin`` and the input config is read from a file:

  .. literalinclude:: config/realize-update-stdin.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-update-stdin.out
     :language: text

* By default, variables/expressions that cannot be rendered are passed through unchanged in the output. For example, given config file ``flowers.yaml`` with contents

  .. literalinclude:: config/flowers.yaml
     :language: yaml
  .. literalinclude:: config/realize-flowers-noop.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-flowers-noop.out
     :language: text

  Adding the ``--total`` flag, however, requires ``uw`` to totally realize the config, and to exit with error status if it cannot:

  .. literalinclude:: config/realize-flowers-total.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-flowers-total.out
     :language: text

* Realization of individual values is all-or-nothing. If a single value contains a mix of renderable and unrenderable variables/expressions, then the entire value remains unrealized. For example, given ``roses.yaml`` with contents

  .. literalinclude:: config/roses.yaml
     :language: yaml
  .. literalinclude:: config/realize-roses-noop.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-roses-noop.out
     :language: text

* To request verbose log output:

  .. literalinclude:: config/realize-verbose.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/realize-verbose.out
     :language: text

  Note that ``uw`` logs to ``stderr`` and writes non-log output to ``stdout``, so the streams can be redirected separately via :shell-redirection:`shell redirection<>`.

.. _cli_config_validate_examples:

``validate``
------------

The ``validate`` action ensures that a given config file is structured properly.

  .. literalinclude:: config/validate-help.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/validate-help.out
     :language: text

Examples
^^^^^^^^

The examples that follow use the :json-schema:`JSON Schema<understanding-json-schema/reference>` file ``schema.jsonschema`` with contents:

.. literalinclude:: config/schema.jsonschema
   :language: json

and the YAML file ``values.yaml`` with contents:

.. literalinclude:: config/values.yaml
   :language: yaml

* To validate a YAML config against a given JSON schema:

  .. literalinclude:: config/validate-pass.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/validate-pass.out
     :language: text

  :shell-redirection:`Shell redirection<>` may also be used to stream output to a file, another process, etc.

* To read the *config* from ``stdin`` and print validation results to ``stdout``:

  .. literalinclude:: config/validate-pass-stdin.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/validate-pass-stdin.out
     :language: text

* If a config fails validation, differences from the schema will be displayed. For example, ``values-bad.yaml``:

  .. literalinclude:: config/values-bad.yaml
     :language: yaml
  .. literalinclude:: config/validate-fail.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/validate-fail.out
     :language: text

* To request verbose log output:

  .. literalinclude:: config/validate-verbose.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/validate-verbose.out
     :language: text

  Note that ``uw`` logs to ``stderr``, so the stream can be :shell-redirection:`redirected<>`.
