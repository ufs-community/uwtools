* Specifying the ``--show-schema`` flag, with no other options, prints the driver's schema:

  .. literalinclude:: show-schema.cmd
     :language: text
     :emphasize-lines: 1
  .. literalinclude:: show-schema.out
     :language: text

* Use the ``--schema-file`` option to specify a custom JSON Schema file with which to validate the driver config. A custom schema could range in complexity from the simplest, most permissive schema, ``{}``, to one based on the built-in schema shown by ``--show-schema``.
