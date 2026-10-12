"""Story 45.6 / 38.2 — daemon-resolved evidence handles and candidates (FR-Q53)."""

from __future__ import annotations

import pytest
from qma.core.plugins import PluginContext
from qma.core.ports.handles import (
    EvidenceHandle,
)
from qma.core.vocabulary.enums import HandleKind
from qma.daemon.plugins import DaemonPluginContext, PluginContextError
from qmf.core import is_ok

KINDS = (
    HandleKind.EXPERIMENT_HANDLE,
    HandleKind.TRADE_LOG_HANDLE,
    HandleKind.KNOWLEDGE_HANDLE,
    HandleKind.MARKET_DATA_HANDLE,
    HandleKind.BACKTEST_HANDLE,
    HandleKind.STRATEGY_HANDLE,
)


def test_plugin_context_cannot_register_handle_kind() -> None:
    ctx = DaemonPluginContext("analysis-backtest")
    assert isinstance(ctx, PluginContext)
    assert not hasattr(PluginContext, "register_handle_kind")
    with pytest.raises(PluginContextError, match="closed qma-core vocabulary"):
        ctx.register_handle_kind("OrderHandle")


def test_handle_payload_round_trip() -> None:
    minted = EvidenceHandle.try_create(
        kind="KnowledgeHandle",
        handle_id="h:know",
        evidence_ref="corpus:snap:1",
    )
    assert is_ok(minted)
    restored = EvidenceHandle.from_payload(minted.value.to_payload())
    assert is_ok(restored)
    assert restored.value.handle_id == "h:know"
    assert restored.value.contents is None
