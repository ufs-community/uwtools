Documentation
=============

Locally Building and Previewing Documentation
---------------------------------------------

To locally build the docs:

#. Obtain a development shell as described in the :doc:`Developer Setup <developer_setup>` section.
#. From the clone root, install the required doc packages: ``source docs/install-deps``
#. Build the docs: ``make docs``

The ``make docs`` command will build the docs under ``docs/build/html``, after which you can preview them in your web browser at the URL

.. code-block:: text

   file://<filesystem-path-to-your-clone>/docs/build/html/index.html

After making and saving changes, re-run ``make docs`` and refresh your browser. Note that some documentation content is dynamically generated: Timestamps shown in e.g. log messages are expected and are ok to commit.

If, at some point, you remove and recreate the conda development environment underlying your development shell, you will need to re-run the ``source install-deps`` command in the new environment/shell. Until then, the installed doc packages will persist and support docs generation.

Viewing Online Documentation
----------------------------

Online documentation generation and hosting for ``uwtools`` is provided by :rtd:`Read the Docs<>`. The green *View Docs* button near the upper right of that page links to the official docs for the project. When viewing the documentation, the version selector at the bottom of the navigation column on the left can be used to switch between the latest development code (``main``), the latest released version (``stable``), and any previously released version.

Docs are also built and temporarily published when Pull Requests (PRs) targeting the ``main`` branch are opened. Visit the :rtd:`Builds page<builds>` to see recent builds, including those made for PRs. Click a PR-related build marked *Passed*, then the small *View docs* link (**not** the large green *View Docs* button) to see the docs built specifically for that PR. See the ``docs/readthedocs.org:uwtools`` item in the checks section near the bottom of the PR for current status of the PR docs build, and click the *Details* link to its right to preview the docs when they are available. Note that if commits are pushed to the PR's source branch, Read the Docs will rebuild the PR docs.

Documentation Guidelines
------------------------

Please follow these guidelines when contributing to the documentation:

* Keep formatting consistent across pages. Update all pages when better ideas are discovered. Otherwise, follow the conventions established in existing content.
* Ensure that the ``make docs`` command completes with no errors or warnings.
* If the link-check portion of ``make docs`` reports that a URL is ``permanently`` redirected, update the link in the docs to use the new URL. Non-permanent redirects can be left as-is.
* Do not manually wrap lines in the ``.rst`` files. Insert newlines only as needed to achieve correctly formatted HTML, and let HTML wrap long lines and/or provide a scrollbar.
* Use one blank line between documentation elements (headers, paragraphs, code blocks, etc.) unless additional lines are necessary to achieve correctly formatted HTML.
* Remove all trailing whitespace, except where inserted by dynamic content generation -- don't fight the tooling.
* In general, avoid pronouns like "we" and "you". (Using "we" may be appropriate when synonymous with "The UW Team", "The UFS Community", etc., when the context is clear.) Prefer direct, factual statements about what the code does, requires, etc.
* Use the `Oxford Comma <https://en.wikipedia.org/wiki/Serial_comma>`_.
* Follow the :rst:`RST Sections<basics.html#sections>` guidelines, underlining section headings with ``=`` characters, subsections with ``-`` characters, and subsubsections with ``^`` characters. If a further level of refinement is needed, indented and/or bulleted lists, as subsections marked with  ``"`` are nearly indistinguishable from those marked with ``^``.
* In [[sub]sub]section titles, capitalize all "principal" words. In practice this usually means all words but articles (a, an, the), logicals (and, etc.), and prepositions (for, of, etc.). Always fully capitalize acronyms (e.g., YAML).
* Never capitalize proper names when their owners do not (e.g., write `"pandas" <https://pandas.pydata.org/>`_, not "Pandas", even at the start of a sentence) or when referring to a software artifact (e.g., write ``numpy`` when referring to the library, and "NumPy" when referring to the project).
* When referring to YAML constructs, `block` refers to an entry whose value is a nested collection of key/value pairs, while `entry` refers to a single key/value pair.
* When using the ``.. code-block::`` directive, align the actual code with the word ``code``. Also, when ``.. code-block::`` directives appear in bulleted or numbered lists, align them with the text following the space to the right of the bullet/number. For example:

  .. code-block:: text

     * Lorem ipsum

       .. code-block:: python

          n = 42

  or

  .. code-block:: text

     #. Lorem ipsum

        .. code-block:: python

           n = 42
