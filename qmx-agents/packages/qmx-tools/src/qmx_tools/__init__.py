"""Task-shaped tools shared by agents and MCP hosts.

`DomainContext` loads on first use, so `python -m qmx_tools.unit_check` checks a file without
importing the service and, through it, qmx-control, QMN and QMB.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qmx_tools.service import DomainContext

__all__ = ["DomainContext"]


def __getattr__(name: str) -> object:
    if name == "DomainContext":
        from qmx_tools.service import DomainContext  # noqa: PLC0415

        return DomainContext
    raise AttributeError(f"module 'qmx_tools' has no attribute {name!r}")
