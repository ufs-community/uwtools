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

Wildcard Support
----------------

Glob-style wildcard patterns are supported when copying and linking and are recognized as such when tagged ``!glob``.

Example block:

.. code-block:: yaml

   a/<afile>: !glob /src/a*
   b/<bfile>: !glob /src/b*

Given ``src/`` directory

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

Wildcards are not supported in combination with HTTP(S) sources.
