
.. _filestager_yaml:

files_to_copy:
^^^^^^^^^^^^^^

See :ref:`this page <files_yaml>` for details.

files_to_hardlink:
^^^^^^^^^^^^^^

Identical to ``files_to_copy:`` except that hard links will be created in the run directory instead of copies, when possible. Otherwise a copy will be created.

files_to_link:
^^^^^^^^^^^^^^

Identical to ``files_to_copy:`` except that symbolic links will be created in the run directory instead of copies.
