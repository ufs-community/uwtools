.. _files_yaml:

File Blocks
===========

Basics
------

File blocks define files to be staged in a target directory as copies or symbolic links. Keys in such blocks specify either absolute destination paths, or destination paths relative to the target directory. Values specify source paths.

Example block:

.. code-block:: yaml

   foo: /path/to/foo
   subdir/bar: /path/to/bar

* Result when copying to target directory ``target/``:

.. code-block:: text

   target
   ├── foo
   └── subdir
       └── bar

where ``foo`` and ``bar`` are copies of their respective source files.

* Result when linking to target directory ``target/``:

.. code-block:: text

   target
   ├── foo -> /path/to/foo
   └── subdir
       └── bar -> /path/to/bar

where ``foo`` and ``bar`` are symbolic links.

.. _files_yaml_glob_support:

Glob Support
------------

Use the ``!glob`` tag to specify that a source-path value should be treated as a :python:`glob <glob.html>` pattern:

Example config:

.. code-block:: yaml

   a/<afile>: !glob /src/a*
   b/<bfile>: !glob /src/b*

Given ``/src/`` directory

.. code-block:: text

   src
   ├── aardvark
   ├── apple
   ├── banana
   ├── bear
   ├── cheetah
   └── cherry

* Result when copying to target directory ``target/``:

.. code-block:: text

   target/
   ├── a
   │   ├── aardvark
   │   └── apple
   └── b
       ├── banana
       └── bear

The behavior when linking is similar.

Note that the destination-path key is treated as a template, with the rightmost component (``<afile>`` and ``<bfile>`` above) discarded and replaced with actual filenames. Since YAML Mapping / Python ``dict`` keys must be unique, this supports the case where the same directory is the target of multiple copies, e.g.

.. code-block:: yaml

   /media/<images>: !glob /some/path/*.jpg
   /media/<videos>: !glob /another/path/*.mp4

A useful convention, adopted here, is to bracket the rightmost component between ``<`` and ``>`` characters as a visual reminder that the component is a placeholder, but this is arbitrary and the brackets have no special meaning.

Since ``uwtools`` passes the argument ``recursive=True`` when calling Python's :python:`iglob() <glob.html#glob.iglob>` to find source files matching the pattern, the following is also supported:

Example config:

.. code-block:: yaml

   <f>: !glob /src/**/a*

Given ``/src/`` directory

.. code-block:: text

   src
   ├── a1
   ├── b1
   ├── bar
   │   ├── a2
   │   ├── b2
   │   └── baz
   │       ├── a3
   │       └── b3
   └── foo
       ├── a4
       └── b4

* Result when copying to target directory ``target/``:

.. code-block:: text

   target
   ├── a1
   ├── bar
   │   ├── a2
   │   └── baz
   │       └── a3
   └── foo
       └── a4

Note that the relative directory structure of the matches source files is retained in the target directory.

Caveats
^^^^^^^

* Glob patterns are not supported in combination with HTTP sources (see below).
* In copy mode, directories identified by a glob pattern are ignored and not copied.
* In link mode, directories identified by a glob pattern are linked.
* Many interesting use cases for copying/linking are beyond the scope of this tool. For more control, including file-grained include and exclude, consider using the unrivaled `rsync <https://rsync.samba.org/>`_, which is available from `conda-forge <https://anaconda.org/conda-forge/rsync>`_ in case your system does not already provide it. It can be called from shell scripts, or via :python:`subprocess <subprocess.html>` from Python.

HTTP Support
------------

Sources values may be ``http://`` or ``https://`` URLs when copying.

Example block:

.. code-block:: yaml

   index: https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.20241001/conus/hrrr.t01z.wrfprsf00.grib2.idx

* Result when copying to target directory ``target/``:

.. code-block:: text

   target
   └── index

HTTP sources and glob patterns are not supported when linking.

HPSS Support
------------

.. _files_yaml_hsi_support:

Full-File ``hsi`` Copies
^^^^^^^^^^^^^^^^^^^^^^^^

Source values may be ``hsi://`` URLs when copying. Note that the ``hsi`` executable must be available on the ``PATH`` of the shell from which ``uw`` (or the application making ``uwtools.api`` calls) is invoked. HPSS sources are not supported when linking.

Example block:

.. code-block:: yaml

   archive.tgz: hsi:///hpss/path/to/archive.tgz

* Result when copying to target directory ``target/``:

.. code-block:: text

   target
   └── archive.tgz

.. _files_yaml_hsi_glob_support:

Glob Support for Full-File ``hsi`` Copies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``!glob`` tag can be used with full-file ``hsi`` copies.

Example block:

.. code-block:: yaml

   <file>: !glob hsi:///hpss/path/to/archive*.tgz

* Result when copying to target directory ``target/``, given HPSS files ``archive1.tgz`` and ``archive2.tgz`` under ``/hpss/path/to/``:

.. code-block:: text

   target
   ├── archive1.tgz
   └── archive2.tgz

Use the following command to preview the files to be copied when using an ``hsi`` glob:

.. code-block:: text

   hsi -q ls -1 '<your-glob-pattern>`

Here, ``<your-glob-pattern>`` is a path that includes wildcard characters, without the ``hsi://`` prefix. See the `HSI Reference Manual <https://hpss-collaboration.org/wp-content/uploads/2023/09/hpss_hsi_10.2_reference_manual.pdf>`_ for more information on ``hsi`` and the wildcard characters it supports in glob patterns.

.. _files_yaml_htar_support:

Archive-Member ``htar`` Copies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Source values may be ``htar://`` URLs when copying. Note that the ``htar``  executable must be available on the ``PATH`` of the shell from which ``uw`` (or the application making ``uwtools.api`` calls) is invoked. HPSS sources are not supported when linking.

The name of the archive member to extract and copy to the destination path on the local filesystem should be provided as the `query string <https://en.wikipedia.org/wiki/Query_string>`_ in the URL, i.e. following ``htar://``, the path to the archive file, and a ``?`` character. If ``?`` or ``&`` characters appear in either the archive-file path or the archive-member path, they should be encoded as ``%3F`` and ``%26``, respectively, per `URL encoding rules <https://developer.mozilla.org/en-US/docs/Glossary/Percent-encoding>`_.

Example block:

.. code-block:: yaml

   foo/b: htar:///hpss/path/to/archive.tar?/internal/path/to/a

* Result when copying to target directory ``target/``:

.. code-block:: text

   target
   └── foo
       └── b

.. _files_yaml_htar_glob_support:

Glob Support for Archive-Member ``htar`` Copies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``!glob`` tag can be used with archive-member ``htar`` copies.

Example block:

.. code-block:: yaml

   <file>: !glob htar:///hpss/path/to/pysrc*.tar?*.py

* Result when copying to target directory ``target/``, given HPSS files ``pysrc1.tar`` and ``pysrc2.tar`` under ``/hpss/path/to/``, where ``pysrc1.tar`` contains member file ``a1.py`` and ``pysrc2.tar`` contains member file ``a2.py``:

.. code-block:: text

   target
   ├── a1.py
   └── a2.py

Caveats
^^^^^^^

* Only a small subset of the functionality available through the ``hsi`` and ``htar`` utilities is exposed via UW YAML. Users with advanced requirements may prefer to use those tools directly, outside ``uwtools``.
