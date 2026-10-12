"""Story 32.3 — daemon binds rungs 1–3; rung 4 stays GAP-0081."""

from __future__ import annotations

from qma.core.plugins import PluginContext
from qma.core.refusals import (
    UiContributionDeferred,
)
from qma.daemon.plugins import (
    DaemonPluginContext,
    PluginLoader,
)
from qmf.core import is_refusal


def _manifest(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "research-corpus",
        "version": "0.1.0",
        "qma_api": ">=0.1.0,<1.0.0",
        "desk": "research",
        "entrypoint": "research_corpus.activate",
        "dependencies": [],
        "contributions": [{"point": "tool", "local_id": "search"}],
        "permissions": [],
        "migrations": [],
    }
    base.update(overrides)
    return base


def _activate(ctx: PluginContext) -> None:
    assert isinstance(ctx, DaemonPluginContext)
    ctx.register_tool("search", {"name": "search"})


def test_loader_refuses_ui_view_as_named_gap_0081_variant() -> None:
    loader = PluginLoader()
    refused = loader.install(
        _manifest(contributions=[{"point": "ui_view", "local_id": "panel"}]),
        activator=_activate,
    )
    assert is_refusal(refused)
    assert UiContributionDeferred.matches(refused)
    assert refused.context["contribution_point"] == "ui_view"
    assert refused.context["gap"] == "GAP-0081"
    assert refused.context["ui_view_minted"] is False
