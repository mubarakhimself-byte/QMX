"""Importers that put files QMX already has into typed price partitions (W9).

Two sources exist off the PC today and both land through the one store commit path, so a
partition imported now is addressed, frozen and corrected exactly like one downloaded
later:

* :mod:`.dukascopy_raw` reads the old raw Dukascopy ``bi5`` hour files through
  ``qmf.data.dukascopy``'s own decoder, which is the only place a bi5 payload is decoded;
* :mod:`.csv_bars` reads the risk-lab one-minute bar CSVs, one side per file.

Both read their source and never write it, and both return the receipt and the quality
note a ``dataset`` card needs.
"""

from __future__ import annotations

from qmf.data.importers.csv_bars import CsvBars, CsvImport, import_csv_month
from qmf.data.importers.dukascopy_raw import RawTicks, RawTicksImport, import_raw_month

__all__ = [
    "CsvBars",
    "CsvImport",
    "RawTicks",
    "RawTicksImport",
    "import_csv_month",
    "import_raw_month",
]
