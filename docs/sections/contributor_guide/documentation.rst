Documentation
=============

Setup
-----

To locally build and preview documentation:

#. Obtain a development shell as described in the :doc:`Developer Setup <developer_setup>` section.
#. 
Guidelines
----------

Please follow these guidelines when contributing to the documentation:

* Ensure that the ``make html`` command completes with no errors or warnings.
* Do not manually wrap lines in the ``.rst`` files. Insert newlines only as needed to achieve correctly formatted HTML, and let HTML handle wrapping long lines.
* Indent ``.. code::`` directives 2 spaces per nesting level to achieve the required alignment. For example, indent 0 spaces for code blocks that should align with text on the left margin, and 2 spaces for code blocks that should align with bulleted or numbered list text. Indent actual code 2 **extra** spaces under the ``.. code::`` directive.
