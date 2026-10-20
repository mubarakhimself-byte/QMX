"""The operator's "last look" cursor: one row in control, a Library log position that only moves
forward, and zero before he has looked once."""

from pathlib import Path

import pytest

from qmx_control.models import ControlError
from qmx_control.service import ControlService


def read(service: ControlService) -> dict[str, object]:
    return service.last_look()


def test_the_cursor_starts_at_zero_moves_forward_and_survives_a_reopen(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    try:
        assert read(service)["position"] == 0
        moved = service.mark_looked(7)
        assert (moved["position"], moved["name"]) == (7, "last_look")
        assert service.mark_looked(3)["position"] == 7
        assert read(service)["at"] is not None
    finally:
        service.close()

    again = ControlService(tmp_path)
    try:
        assert read(again)["position"] == 7
        with pytest.raises(ControlError) as refused:
            again.mark_looked(-1)
        assert refused.value.code == "invalid_cursor"
    finally:
        again.close()
