<!-- Source: https://raw.githubusercontent.com/python/cpython/3.14/Doc/whatsnew/3.14.rst
     Fetched: 2026-10-28. Excerpt: the PEP 784 (Zstandard) section, verbatim. -->

.. _whatsnew314-zstandard:

:pep:`784`: Zstandard support in the standard library
-----------------------------------------------------

The new :mod:`compression` package contains modules :mod:`!compression.lzma`,
:mod:`!compression.bz2`, :mod:`!compression.gzip` and :mod:`!compression.zlib`
which re-export the :mod:`lzma`, :mod:`bz2`, :mod:`gzip` and :mod:`zlib`
modules respectively. The new import names under :mod:`!compression` are the
preferred names for importing these compression modules from Python 3.14. However,
the existing modules names have not been deprecated. Any deprecation or removal
of the existing compression modules will occur no sooner than five years after
the release of 3.14.

The new :mod:`compression.zstd` module provides compression and decompression
APIs for the Zstandard format via bindings to `Meta's zstd library
<https://facebook.github.io/zstd/>`__. Zstandard is a widely adopted, highly
efficient, and fast compression format. In addition to the APIs introduced in
:mod:`!compression.zstd`, support for reading and writing Zstandard compressed
archives has been added to the :mod:`tarfile`, :mod:`zipfile`, and
:mod:`shutil` modules.

Here's an example of using the new module to compress some data:

.. code-block:: python

    from compression import zstd
    import math

    data = str(math.pi).encode() * 20
    compressed = zstd.compress(data)
    ratio = len(compressed) / len(data)
    print(f"Achieved compression ratio of {ratio}")

As can be seen, the API is similar to the APIs of the :mod:`!lzma` and
:mod:`!bz2` modules.

(Contributed by Emma Harper Smith, Adam Turner, Gregory P. Smith, Tomas Roun,
Victor Stinner, and Rogdham in :gh:`132983`.)

.. seealso:: :pep:`784`.


.. _whatsnew314-asyncio-introspection:

Asyncio introspection capabilities
