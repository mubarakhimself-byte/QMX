"""The built-in memory provider's seam (AD-18).

The port lives in `qmx_engine.ports.memory`; the engine that answers it is
`qmx_memory.RecallEngine`, which depends on this package, so the wiring runs one way: the host
installs its engine here before the engine's door opens, and the port the engine was handed
answers with it.

    qmx_engine.memory.install(recall_engine, library=adapter)
    ...
    qmx_engine.memory.install(None)
"""

from qmx_engine.ports.memory import MemoryPort, MemoryStub, install, installed

__all__ = ["MemoryPort", "MemoryStub", "install", "installed"]
