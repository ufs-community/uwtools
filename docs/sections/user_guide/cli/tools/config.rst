``config``
==========

The ``uw`` mode for handling configuration files (configs).

.. literalinclude:: config/help.cmd
   :emphasize-lines: 1
.. literalinclude:: config/help.out
   :language: text

.. _cli_config_compare_examples:

``compare``
-----------

The ``compare`` action lets users compare two config files.

.. literalinclude:: config/compare-help.cmd
   :emphasize-lines: 1
.. literalinclude:: config/compare-help.out
   :language: text

Examples
^^^^^^^^

The examples that follow use namelist files ``a.nml`` and ``b.nml``, both initially with the following contents:

.. literalinclude:: config/a.nml
   :language: fortran

* To compare two config files with the same contents:

  .. literalinclude:: config/compare-match.cmd
     :emphasize-lines: 1
  .. literalinclude:: config/compare-match.out
     :language: text

* If there are differences between the config files, they will be shown below the dashed line. For example, ``c.nml`` is missing the line ``recipient: World``:

  .. literalinclude:: config/compare-diff.cmd
     :emphasize-lines: 1
  .. literalinclude:: config/compare-diff.out
     :language: text

* If a config file has an unrecognized (or no) extension, ``uw`` will not know how to parse its contents:

  .. literalinclude:: config/compare-bad-extension.cmd
     :emphasize-lines: 1
  .. literalinclude:: config/compare-bad-extension.out
     :language: text

  In this case, the format can be explicitly specified (``a.txt`` is a copy of ``a.nml``):

  .. literalinclude:: config/compare-bad-extension-fix.cmd
     :emphasize-lines: 1
  .. literalinclude:: config/compare-bad-extension-fix.out
     :language: text

* To request verbose log output:

  .. literalinclude:: config/compare-verbose.cmd
     :emphasize-lines: 1
  .. literalinclude:: config/compare-verbose.out
     :language: text

  Note that ``uw`` logs to ``stderr``. Use `shell redirection <https://www.gnu.org/software/bash/manual/html_node/Redirections.html>`_ as needed.

.. note:: Comparisons are supported only for configs of the same format, e.g. YAML vs YAML, Fortran namelist vs Fortran namelist, etc. ``uw`` will flag invalid comparisons:

   .. literalinclude:: config/compare-format-mismatch.cmd
      :emphasize-lines: 1
   .. literalinclude:: config/compare-format-mismatch.out
      :language: text

.. _cli_config_realize_examples:

``realize``
-----------

In ``uw`` terminology, to realize a configuration file is to transform it from its raw form into its final, usable state. The ``realize`` action can build a complete config file from two or more separate files.

.. code-block:: text

   $ uw config realize --help
   usage: uw config realize [-h] [--version] [--input-file PATH] [--input-format {ini,nml,sh,yaml}]
                            [--output-file PATH] [--output-format {ini,nml,sh,yaml}]
                            [--output-block KEY[.KEY[.KEY]...]] [--values-needed] [--total]
                            [--dry-run] [--quiet] [--verbose]
                            [PATH ...]

   Realize config

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit
     --input-file PATH, -i PATH
         Path to input file (defaults to stdin)
     --input-format {ini,nml,sh,yaml}
         Input format
     --output-file PATH, -o PATH
         Path to output file (defaults to stdout)
     --output-format {ini,nml,sh,yaml}
         Output format
     --output-block KEY[.KEY[.KEY]...]
         Dot-separated path of keys to the block to be output
     --values-needed
         Print report of values needed to render template
     --total
         Require rendering of all Jinja2 variables/expressions
     --dry-run
         Only log info, making no changes
     --quiet, -q
         Print no logging messages
     --verbose, -v
         Print all logging messages
     PATH
         Additional files to supplement primary input

Examples
^^^^^^^^

The examples in this section use the YAML file ``config.yaml`` with the following contents:

.. code-block:: yaml

   values:
     date: '{{ yyyymmdd }}'
     empty:
     greeting: Hello
     message: '{{ (greeting + " " + recipient + " ") * repeat }}'
     recipient: World
     repeat: 1

and the supplemental YAML file ``values1.yaml`` with the following contents:

.. code-block:: yaml

   values:
     date: 20240105
     greeting: Good Night
     recipient: Moon
     repeat: 2

and an additional supplemental YAML file ``values2.yaml`` with the following contents:

.. code-block:: yaml

   values:
     empty: false
     repeat: 3

* To show the values in the input config file that have unrendered Jinja2 variables/expressions or empty keys:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-format yaml --values-needed
     [2024-01-23T22:28:40]     INFO Keys that are complete:
     [2024-01-23T22:28:40]     INFO     values
     [2024-01-23T22:28:40]     INFO     values.greeting
     [2024-01-23T22:28:40]     INFO     values.message
     [2024-01-23T22:28:40]     INFO     values.recipient
     [2024-01-23T22:28:40]     INFO     values.repeat
     [2024-01-23T22:28:40]     INFO
     [2024-01-23T22:28:40]     INFO Keys with unrendered Jinja2 variables/expressions:
     [2024-01-23T22:28:40]     INFO     values.date: {{ yyyymmdd }}
     [2024-01-23T22:28:40]     INFO
     [2024-01-23T22:28:40]     INFO Keys that are set to empty:
     [2024-01-23T22:28:40]     INFO     values.empty

* To realize the config to ``stdout``, a target output format must be explicitly specified:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-format yaml
     values:
       date: '{{ yyyymmdd }}'
       empty: null
       greeting: Hello
       message: 'Hello World '
       recipient: World
       repeat: 1

  Shell redirection via ``|``, ``>``, et al. may also be used to stream output to a file, another process, etc.

* Values in the input file can be overridden via one or more supplemental files specified as positional arguments. Priority increases from left to right.

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-format yaml values1.yaml values2.yaml
     values:
       date: 20240105
       empty: false
       greeting: Good Night
       message: 'Good Night Moon Good Night Moon Good Night Moon '
       recipient: Moon
       repeat: 3

* To realize the config to a file via command-line argument:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-file realized.yaml values1.yaml

  The contents of ``realized.yaml``:

  .. code-block:: yaml

     values:
       date: 20240105
       empty: null
       greeting: Good Night
       message: 'Good Night Moon Good Night Moon '
       recipient: Moon
       repeat: 2

* By default, variables/expressions that cannot be rendered are passed through unchanged in the output. For example, given config file ``config.yaml`` with contents

  .. code-block:: yaml

     roses: "{{ color1 }}"
     violets: "{{ color2 }}"
     color1: red

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-format yaml values.yaml
     roses: red
     violets: '{{ color2 }}'
     color1: red
     $ echo $?
     0

  Adding the ``--total`` flag, however, requires ``uw`` to totally realize the config, and to exit with error status if it cannot:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-format yaml values.yaml --total
     [2024-04-02T00:53:04]    ERROR Config could not be realized. Try with --values-needed for details.
     $ echo $?
     1

* Realization of individual values is all-or-nothing. If a single value contains a mix of renderable and unrenderable variables/expressions, then the entire value remains unrealized. For example, given ``config.yaml`` with contents

  .. code-block:: yaml

     roses: "{{ color1 }} or {{ color2 }}"
     color1: red

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-format yaml
     roses: '{{ color1 }} or {{ color2 }}'
     color1: red

* With the ``--dry-run`` flag specified, nothing is written to ``stdout`` (or to a file if ``--output-file`` is specified), but a report of what would have been written is logged to ``stderr``:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-file realized.yaml --dry-run values1.yaml
     [2024-01-23T22:31:08]     INFO values:
     [2024-01-23T22:31:08]     INFO   date: 20240105
     [2024-01-23T22:31:08]     INFO   empty: null
     [2024-01-23T22:31:08]     INFO   greeting: Good Night
     [2024-01-23T22:31:08]     INFO   message: 'Good Night Moon Good Night Moon '
     [2024-01-23T22:31:08]     INFO   recipient: Moon
     [2024-01-23T22:31:08]     INFO   repeat: 2

* If an input file is read alone from ``stdin``, ``uw`` will not know how to parse its contents:

  .. code-block:: text

     $ cat config.yaml | uw config realize --output-file realized.yaml values1.yaml
     Specify --input-format when --input-file is not specified

* To read the config from ``stdin`` and realize to ``stdout``:

  .. code-block:: text

     $ cat config.yaml | uw config realize --input-format yaml --output-format yaml values1.yaml
     values:
       date: 20240105
       empty: null
       greeting: Good Night
       message: 'Good Night Moon Good Night Moon '
       recipient: Moon
       repeat: 2

* To read the config from ``stdin`` and realize a subsection to ``stdout`` in a different format:

  .. code-block:: text

     $ cat config.yaml | uw config realize --input-format yaml --output-format sh --output-block values values1.yaml
     date=20240105
     empty=None
     greeting='Good Night'
     message='Good Night Moon Good Night Moon '
     recipient=Moon
     repeat=2

* If the config file has an unrecognized (or no) extension, ``uw`` will not know how to parse its contents:

  .. code-block:: text

     $ uw config realize --input-file config.txt --output-format yaml values1.yaml
     Cannot deduce format of 'config.txt' from unknown extension 'txt'

  In this case, the format can be explicitly specified  (``config.txt`` is a copy of ``config.yaml``):

  .. code-block:: text

     $ uw config realize --input-file config.txt --input-format yaml --output-format yaml values1.yaml
     values:
       date: 20240105
       empty: null
       greeting: Good Night
       message: 'Good Night Moon Good Night Moon '
       recipient: Moon
       repeat: 2

* To request verbose log output:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-format yaml --verbose values1.yaml
     [2024-01-23T22:59:58]    DEBUG Command: uw config realize --input-file config.yaml --output-format yaml --verbose values1.yaml
     [2024-01-23T22:59:58]    DEBUG Before update, config has depth 2
     [2024-01-23T22:59:58]    DEBUG Supplemental config has depth 2
     [2024-01-23T22:59:58]    DEBUG After update, config has depth 2
     [2024-01-23T22:59:58]    DEBUG Dereferencing, current value:
     [2024-01-23T22:59:58]    DEBUG   values:
     [2024-01-23T22:59:58]    DEBUG     date: 20240105
     [2024-01-23T22:59:58]    DEBUG     empty: null
     [2024-01-23T22:59:58]    DEBUG     greeting: Good Night
     [2024-01-23T22:59:58]    DEBUG     message: '{{ (greeting + " " + recipient + " ") * repeat }}'
     [2024-01-23T22:59:58]    DEBUG     recipient: Moon
     [2024-01-23T22:59:58]    DEBUG     repeat: 2
     ...
     [2024-01-23T22:59:58]    DEBUG Dereferencing, final value:
     [2024-01-23T22:59:58]    DEBUG   values:
     [2024-01-23T22:59:58]    DEBUG     date: 20240105
     [2024-01-23T22:59:58]    DEBUG     empty: null
     [2024-01-23T22:59:58]    DEBUG     greeting: Good Night
     [2024-01-23T22:59:58]    DEBUG     message: 'Good Night Moon Good Night Moon '
     [2024-01-23T22:59:58]    DEBUG     recipient: Moon
     [2024-01-23T22:59:58]    DEBUG     repeat: 2
     values:
       date: 20240105
       empty: null
       greeting: Good Night
       message: 'Good Night Moon Good Night Moon '
       recipient: Moon
       repeat: 2

  Note that ``uw`` logs to ``stderr`` and writes non-log output to ``stdout``, so the streams can be redirected separately:

  .. code-block:: text

     $ uw config realize --input-file config.yaml --output-format yaml --verbose values1.yaml >realized.yaml 2>realized.log

  The contents of ``realized.yaml``:

  .. code-block:: yaml

     values:
       date: 20240105
       empty: null
       greeting: Good Night
       message: 'Good Night Moon Good Night Moon '
       recipient: Moon
       repeat: 2

  The contents of ``realized.log``:

  .. code-block:: text

     [2024-01-23T23:01:23]    DEBUG Command: uw config realize --input-file config.yaml --output-format yaml --verbose values1.yaml
     [2024-01-23T23:01:23]    DEBUG Before update, config has depth 2
     [2024-01-23T23:01:23]    DEBUG Supplemental config has depth 2
     [2024-01-23T23:01:23]    DEBUG After update, config has depth 2
     [2024-01-23T23:01:23]    DEBUG Dereferencing, current value:
     [2024-01-23T23:01:23]    DEBUG   values:
     [2024-01-23T23:01:23]    DEBUG     date: 20240105
     [2024-01-23T23:01:23]    DEBUG     empty: null
     [2024-01-23T23:01:23]    DEBUG     greeting: Good Night
     [2024-01-23T23:01:23]    DEBUG     message: '{{ (greeting + " " + recipient + " ") * repeat }}'
     [2024-01-23T23:01:23]    DEBUG     recipient: Moon
     [2024-01-23T23:01:23]    DEBUG     repeat: 2
     [2024-01-23T23:01:23]    DEBUG [dereference] Accepting: 20240105
     [2024-01-23T23:01:23]    DEBUG [dereference] Accepting: None
     [2024-01-23T23:01:23]    DEBUG [dereference] Rendering: Good Night
     [2024-01-23T23:01:23]    DEBUG [dereference] Rendered: Good Night
     [2024-01-23T23:01:23]    DEBUG [dereference] Rendering: {{ (greeting + " " + recipient + " ") * repeat }}
     [2024-01-23T23:01:23]    DEBUG [dereference] Rendered: Good Night Moon Good Night Moon
     [2024-01-23T23:01:23]    DEBUG [dereference] Rendering: Moon
     [2024-01-23T23:01:23]    DEBUG [dereference] Rendered: Moon
     [2024-01-23T23:01:23]    DEBUG [dereference] Accepting: 2
     ...
     [2024-01-23T23:01:23]    DEBUG Dereferencing, final value:
     [2024-01-23T23:01:23]    DEBUG   values:
     [2024-01-23T23:01:23]    DEBUG     date: 20240105
     [2024-01-23T23:01:23]    DEBUG     empty: null
     [2024-01-23T23:01:23]    DEBUG     greeting: Good Night
     [2024-01-23T23:01:23]    DEBUG     message: 'Good Night Moon Good Night Moon '
     [2024-01-23T23:01:23]    DEBUG     recipient: Moon
     [2024-01-23T23:01:23]    DEBUG     repeat: 2

.. note:: Combining configs with incompatible depths is not supported. ``ini`` and ``nml`` configs are depth-2, as they organize their key-value pairs (one level) under top-level sections or namelists (a second level). ``sh`` configs are depth-1, and ``yaml`` configs have arbitrary depth.

   For example, when attempting to generate a ``sh`` config from a depth-2 ``yaml``:

   .. code-block:: text

      $ uw config realize --input-file config.yaml --output-format sh
      [2024-01-23T23:02:42]    ERROR Cannot realize depth-2 config to type-'sh' config
      Cannot realize depth-2 config to type-'sh' config

.. note:: In recognition of the different sets of value types representable in each config format, ``uw`` supports two format-combination schemes:

   1. **Output matches input:** The format of the output config matches that of the input config.
   2. **YAML:** YAML is accepted as either input or output with any other format. In the worst case, values always have a string representation, but note that, for example, the string representation of a YAML sequence (Python ``list``) in an INI output config may not be useful.

   In all cases, any supplemental configs must be in the same format as the input config and must have recognized extensions.

   ``uw`` considers invalid combination requests errors:

   .. code-block:: text

      $ uw config realize --input-file b.nml --output-file a.ini
      Accepted output formats for input format nml are nml or yaml

   .. code-block:: text

      $ uw config realize --input-file a.yaml --output-file c.yaml b.nml
      Supplemental config #1 format nml must match input format yaml

.. _cli_config_validate_examples:

``validate``
------------

The ``validate`` action ensures that a given config file is structured properly.

.. code-block:: text

   $ uw config validate --help
   usage: uw config validate --schema-file PATH [-h] [--version] [--input-file PATH] [--quiet]
                             [--verbose]

   Validate config

   Required arguments:
     --schema-file PATH
         Path to schema file to use for validation

   Optional arguments:
     -h, --help
         Show help and exit
     --version
         Show version info and exit
     --input-file PATH, -i PATH
         Path to input file (defaults to stdin)
     --quiet, -q
         Print no logging messages
     --verbose, -v
         Print all logging messages

Examples
^^^^^^^^

The examples that follow use the :json-schema:`JSON Schema<understanding-json-schema/reference>` file ``schema.jsonschema`` with the following contents:

.. code-block:: json

   {
     "$schema": "http://json-schema.org/draft-07/schema#",
     "type": "object",
     "properties": {
       "values": {
         "type": "object",
         "properties": {
           "greeting": {
             "type": "string"
           },
           "recipient": {
             "type": "string"
           }
         },
         "required": ["greeting", "recipient"],
         "additionalProperties": false
       }
     },
     "required": ["values"],
     "additionalProperties": false
   }

and the YAML file ``values.yaml`` with the following contents:

.. code-block:: yaml

   values:
     greeting: Hello
     recipient: World

* To validate a YAML config against a given JSON schema:

  .. code-block:: text

     $ uw config validate --schema-file schema.jsonschema --input-file values.yaml
     [2024-01-03T17:23:07]     INFO 0 UW schema-validation errors found

  Shell redirection via ``|``, ``>``, et al. may also be used to stream output to a file, another process, etc.

* To read the *config* from ``stdin`` and print validation results to ``stdout``:

  .. code-block:: text

     $ cat values.yaml | uw config validate --schema-file schema.jsonschema
     [2024-01-03T17:26:29]     INFO 0 UW schema-validation errors found

* However, reading the *schema* from ``stdin`` is **not** supported:

  .. code-block:: text

     $ cat schema.jsonschema | uw config validate --input-file values.yaml
     uw config validate: error: the following arguments are required: --schema-file

* If a config fails validation, differences from the schema will be displayed. For example, with ``recipient: World`` removed from ``values.yaml``:

  .. code-block:: text

     $ uw config validate --schema-file schema.jsonschema --input-file values.yaml
     [2024-01-03T17:31:19]    ERROR 1 UW schema-validation error found
     [2024-01-03T17:31:19]    ERROR 'recipient' is a required property
     [2024-01-03T17:31:19]    ERROR
     [2024-01-03T17:31:19]    ERROR Failed validating 'required' in schema['properties']['values']:
     [2024-01-03T17:31:19]    ERROR     {'additionalProperties': False,
     [2024-01-03T17:31:19]    ERROR      'properties': {'greeting': {'type': 'string'},
     [2024-01-03T17:31:19]    ERROR                     'recipient': {'type': 'string'}},
     [2024-01-03T17:31:19]    ERROR      'required': ['greeting', 'recipient'],
     [2024-01-03T17:31:19]    ERROR      'type': 'object'}
     [2024-01-03T17:31:19]    ERROR
     [2024-01-03T17:31:19]    ERROR On instance['values']:
     [2024-01-03T17:31:19]    ERROR     {'greeting': 'Hello'}

* To request verbose log output:

  .. code-block:: text

     $ uw config validate --schema-file schema.jsonschema --input-file values.yaml --verbose
     [2024-01-03T17:29:46]    DEBUG Command: uw config validate --schema-file schema.jsonschema --input-file values.yaml --verbose
     [2024-01-03T17:29:46]    DEBUG Dereferencing, initial value: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
     [2024-01-03T17:29:46]    DEBUG Rendering: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
     [2024-01-03T17:29:46]    DEBUG Rendering: {'greeting': 'Hello', 'recipient': 'World'}
     [2024-01-03T17:29:46]    DEBUG Rendering: Hello
     [2024-01-03T17:29:46]    DEBUG Rendering: World
     [2024-01-03T17:29:46]    DEBUG Dereferencing, final value: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
     [2024-01-03T17:29:46]     INFO 0 UW schema-validation errors found

  Note that ``uw`` logs to ``stderr``, so the stream can be redirected:

  .. code-block:: text

     $ uw config validate --schema-file schema.jsonschema --input-file values.yaml --verbose 2>validate.log

  The contents of ``validate.log``:

  .. code-block:: text

     [2024-01-03T17:30:49]    DEBUG Command: uw config validate --schema-file schema.jsonschema --input-file values.yaml --verbose
     [2024-01-03T17:30:49]    DEBUG Dereferencing, initial value: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
     [2024-01-03T17:30:49]    DEBUG Rendering: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
     [2024-01-03T17:30:49]    DEBUG Rendering: {'greeting': 'Hello', 'recipient': 'World'}
     [2024-01-03T17:30:49]    DEBUG Rendering: Hello
     [2024-01-03T17:30:49]    DEBUG Rendering: World
     [2024-01-03T17:30:49]    DEBUG Dereferencing, final value: {'values': {'greeting': 'Hello', 'recipient': 'World'}}
     [2024-01-03T17:30:49]     INFO 0 UW schema-validation errors found
