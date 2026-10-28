<!-- Source: https://raw.githubusercontent.com/borgbackup/borg/1.4-maint/docs/usage/compact.rst
     Fetched: 2026-10-28 (verbatim copy of the primary source file) -->

.. include:: compact.rst.inc

Examples
~~~~~~~~
::

    # compact segments and free repo disk space
    $ borg compact /path/to/repo

    # same as above plus clean up 17-byte commit-only segments
    $ borg compact --cleanup-commits /path/to/repo


