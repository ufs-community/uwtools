``config``
==========

.. contents::
   :backlinks: top
   :depth: 1
   :local:

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

  Note that ``uw`` logs to ``stderr``. Use shell redirection as needed.

.. note:: Comparisons are supported only for configs of the same format, e.g. YAML vs YAML, Fortran namelist vs Fortran namelist, etc. ``uw`` will flag invalid comparisons:

  .. literalinclude:: config/compare-format-mismatch.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/compare-format-mismatch.out
     :language: text

.. _cli_config_compose_examples:

``compose``
-----------

The ``compose`` action builds up a final config by repeatedly updating a base config with the contents of other configs of the same format.

.. literalinclude:: config/compose-help.cmd
   :language: text
   :emphasize-lines: 1
.. literalinclude:: config/compose-help.out
   :language: text

Examples
^^^^^^^^

* Consider three YAML configs:

  .. literalinclude:: config/compose-base.yaml
     :caption: compose-base.yaml
     :language: yaml
  .. literalinclude:: config/compose-update-1.yaml
     :caption: compose-update-1.yaml
     :language: yaml
  .. literalinclude:: config/compose-update-2.yaml
     :caption: compose-update-2.yaml
     :language: yaml

  Compose the three together, writing to ``stdout``:

  .. literalinclude:: config/compose-basic.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/compose-basic.out
     :language: yaml

  Values provided by update configs override or augment values provided in the base config, while unaffected values survive to the final config. Priority of values increases from left to right.

  Additionally:

    * Sets of configs in the ``ini``, ``nml``, and ``sh`` formats can be similarly composed.
    * The ``--input-format`` and ``--output-format`` options can be used to specify the format of the input and output configs, respectively, for cases when ``uwtools`` cannot deduce the format of configs from their filename extensions. When the formats are neither explicitly specified or deduced, ``yaml`` is assumed.
    * The ``--output-file`` / ``-o`` option can be added to write the final config to a file instead of to ``stdout``.

* The optional ``--realize`` switch can be used to render as many Jinja2 template expressions as possible in the final config, using the config itself as a source of values. These may be supplemented with the optional ``--cycle`` and/or ``--leadtime`` command-line arguments, which inject Python ``datetime`` and ``timedelta`` objects, respectively, as values for use in Jinja2 expressions. For example:

  .. literalinclude:: config/compose-template.yaml
     :caption: compose-template.yaml
     :language: yaml
  .. literalinclude:: config/compose-values.yaml
     :caption: compose-values.yaml
     :language: yaml

  Without the ``--realize`` switch:

  .. literalinclude:: config/compose-realize-no.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/compose-realize-no.out
     :language: yaml

  And with ``--realize``, ``--cycle``, and ``--leadtime``:

  .. literalinclude:: config/compose-realize-yes.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/compose-realize-yes.out
     :language: yaml

* The ``compose`` action supports defining YAML `anchors and aliases <https://support.atlassian.com/bitbucket-cloud/docs/yaml-anchors/>`_ in separate files, something not supported natively by the underlying `PyYAML <https://pyyaml.org/>`_ library. For example:

  .. literalinclude:: config/alias.yaml
     :caption: alias.yaml
     :language: yaml
  .. literalinclude:: config/anchor.yaml
     :caption: anchor.yaml
     :language: yaml
  .. literalinclude:: config/compose-anchor-alias.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/compose-anchor-alias.out
     :language: yaml

  This example is trivial, but a YAML-anchored block could provide many more configuration values, and an alias to that block could be repeated many times in a config, or across many configs, avoiding hard-to-maintain and error-prone repeated values.

.. note:: Anchor names must be unique across all files passed to ``uw config compose``, as YAML does not permit repetition of anchor names.

.. note:: Anchors must be defined either in the current file, or in a file that follows the current file in the list of YAML configs to compose. For example, given the invocation ``uw config compose 1.yaml 2.yaml 3.yaml``, if ``*A`` appears in ``1.yaml``, then ``&A`` may be defined in any one of the three YAML files. If, ``*A`` appears instead in ``2.yaml``, then ``&A`` must be defined either in ``2.yaml`` or ``3.yaml``. And if ``*A`` appears in ``3.yaml``, then ``&A`` must be defined in ``3.yaml``.

* Configs in any format supported by ``uwtools`` can be composed, but all composed configs must be of the same format. For example, Fortran namelist configs may be composed:

  .. literalinclude:: config/compose-base.nml
     :caption: compose-base.nml
     :language: fortran
  .. literalinclude:: config/compose-update-1.nml
     :caption: compose-update-1.nml
     :language: fortran
  .. literalinclude:: config/compose-update-2.nml
     :caption: compose-update-2.nml
     :language: fortran
  .. literalinclude:: config/compose-nml.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/compose-nml.out
     :language: fortran

.. _cli_config_realize_examples:

``realize``
-----------

In ``uw`` terminology, to realize a configuration file is to transform it from its raw form into its final, usable state. The ``realize`` action can build a complete config file from two or more separate files.

.. literalinclude:: config/realize-help.cmd
   :language: text
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

  Shell redirection may also be used to stream output to a file, another process, etc.

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

* The optional ``--cycle`` and ``--leadtime`` arguments may be used to inject Python ``datetime`` and ``timedelta`` objects, respecticely, into the config for use in Jinja2 expressions. For example, the YAML config

  .. literalinclude:: config/cycle-leadtime.yaml
     :language: yaml

  can be realized with

  .. literalinclude:: config/cycle-leadtime-yaml.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: config/cycle-leadtime-yaml.out
     :language: text

  The ``cycle`` and ``leadtime`` values can also be used with Fortran namelist, INI, and shell key-value pair configs.

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

.. note:: Combining configs with incompatible depths is not supported. ``ini`` configs are depth-2, as they organize their key-value pairs (one level) under top-level sections (a second level). ``sh`` configs are depth-1, and ``yaml`` configs have arbitrary depth.

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

  Note that ``uw`` logs to ``stderr`` and writes non-log output to ``stdout``, so the streams can be redirected separately via shell redirection.

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

  Shell redirection may also be used to stream output to a file, another process, etc.

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

  Note that ``uw`` logs to ``stderr``, so the stream can be redirected.
