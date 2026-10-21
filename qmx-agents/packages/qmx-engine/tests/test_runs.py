"""`runs.start` runs only a published version, and published means on `main` (AD-11, L-51)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import cast

import pytest
from flows import CHAIN

from qmx_engine.ports.library import Bundle, runs_ref
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Refused


def test_only_a_version_on_main_runs_live(tmp_path: Path) -> None:
    with EngineService.open(tmp_path) as svc:
        draft = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR)
        stored = svc.ctx.library.get(draft.object_id)
        library = cast(LibraryFake, svc.ctx.library)
        on_a_run = library._put(  # pyright: ignore[reportPrivateUsage]
            "workflow",
            draft.item,
            runs_ref("run-elsewhere"),
            dict(stored.fields),
            "run:run-elsewhere",
            stored.blob,
        )
        refused: list[tuple[str, bool]] = []
        for object_id in (draft.object_id, on_a_run.object_id):
            with pytest.raises(Refused) as caught:
                asyncio.run(svc.runs.start(object_id, caller=OPERATOR))
            refused.append((caught.value.code, " is draft;" in str(caught.value)))
        asyncio.run(svc.tests.run(draft.item, caller=OPERATOR))
        version = svc.versions.publish(draft.item, "1.0.0", caller=OPERATOR)
        ran = asyncio.run(svc.runs.start(version, caller=OPERATOR))

    assert refused == [("run_refused", True), ("run_refused", True)]
    assert (ran.mode, ran.status) == ("live", "passed")
