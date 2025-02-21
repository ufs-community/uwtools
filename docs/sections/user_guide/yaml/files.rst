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

.. _files_yaml_glob_support:

Glob Support
------------

Use the ``!glob`` tag to specify that a source-path value should be treated as a glob pattern:

Example block:

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

Glob patterns are not supported in combination with HTTP(S) sources.

Note that the destination-path key is treated as a template, with the rightmost component (``<afile>`` and ``<bfile>`` above) discarded and replaced with actual filenames. Since YAML Mapping / Python ``dict`` keys must be unique, this supports the case where the same directory is the target of multiple copies, e.g.

.. code-block:: yaml

   /media/<images>: !glob /some/path/*.jpg
   /media/<videos>: !glob /another/path/*.mp4

A useful convention, adopted here, is to bracket the rightmost component between ``<`` and ``>`` characters as a visual reminder that the component is a placeholder, but this is arbitrary and the brackets have no special meaning.
