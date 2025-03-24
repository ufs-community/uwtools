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

Behavior is similar when linking.

Note that the destination-path key is treated as a template, with the rightmost component (``<afile>`` and ``<bfile>`` above) discarded and replaced with actual filenames. Since YAML Mapping / Python ``dict`` keys must be unique, this supports the case where the same directory is the target of multiple copies, e.g.

.. code-block:: yaml

   /media/<images>: !glob /some/path/*.jpg
   /media/<videos>: !glob /another/path/*.mp4

A useful convention, adopted here, is to bracket the rightmost component between ``<`` and ``>`` characters as a visual reminder that the component is a placeholder, but this is arbitrary and the brackets have no special meaning.

Since ``uwtools`` passes argument ``recursive=True`` when calling Python's :python:`iglob() <glob.html#glob.iglob>`, the following behavior is also supported:

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

Caveats
^^^^^^^

* Glob patterns are not supported in combination with HTTP(S) sources.
* In copy mode, directories identified by a glob pattern are ignored and not copied.
* In link mode, directories identified by a glob pattern are linked.
* Many interesting use cases for copying/linking are beyond the scope of this tool. For more control, including file-grained include and exclude, consider using the unrivaled `rsync <https://rsync.samba.org/>`_, which can be installed from conda in case your system does not already provide it. It can be called from shell scripts, or via :python:`subprocess <subprocess.html>` from Python.

HTTP(S) Support
---------------

Sources values may be ``http://`` or ``https://`` URLs when copying.

Example block:

.. code-block:: yaml

   index: https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.20241001/conus/hrrr.t01z.wrfprsf00.grib2.idx

* Result when copying to target directory ``target/``:

.. code-block:: text

   target
   └── index

HTTP(S) sources are not supported when linking.

HPSS Support
------------

Full-file copies with ``hsi``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Source values may be ``hsi://`` URLs when copying. Note that the ``hsi`` executable must be available on the ``PATH`` of the shell from which ``uw`` (or the application making ``uwtools.api`` calls) is invoked.

Example block:

.. code-block:: yaml

   archive.tgz: hsi:///hpss/path/to/archive.tgz

* Result when copying to target directory ``target/``:

.. code-block:: text

   target
   └── archive.tgz

HPSS sources are not supported when linking.

.. _files_yaml_hsi_glob_support:

The ``!glob`` tag (see :ref:`here<files_yaml_glob_support>`) can be used with full-file ``hsi`` copies. For example:

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

Here, ``<your-glob-pattern>`` is a plain path, including wildcard characters, without the ``hsi://`` prefix.
