"""A pack's operations are catalog rows on the `app:<id>` toolset, and a ring of asks is bounded
by the host's `call_depth` (AD-61, AD-64)."""

from __future__ import annotations

import pytest

from qmx_control.catalog import (
    CatalogError,
    app_rows,
    app_toolset,
    check,
    dispatch_refusal,
    node_types,
    rows,
)

OPERATIONS = {
    "bias": {"approval": "read", "returns": "artifact", "description": "Read the daily bias."},
    "summarize": {"approval": "domain_write", "returns": "artifact", "state": "instance"},
}


def test_a_packs_rows_are_its_declared_operations_pinned_to_its_version() -> None:
    found = app_rows("macro-daily-bias", "1.2.0", OPERATIONS)
    assert [(row.name, row.wire, row.id) for row in found] == [
        ("app:macro-daily-bias_bias", "app_macro-daily-bias_bias", "macro-daily-bias.bias"),
        (
            "app:macro-daily-bias_summarize",
            "app_macro-daily-bias_summarize",
            "macro-daily-bias.summarize",
        ),
    ]
    assert [(row.toolset, row.pack, row.owner, row.version) for row in found] == [
        (app_toolset("macro-daily-bias"), "macro-daily-bias", "macro-daily-bias", "1.2.0"),
        (app_toolset("macro-daily-bias"), "macro-daily-bias", "macro-daily-bias", "1.2.0"),
    ]
    assert [row.approval for row in found] == ["read", "domain_write"]
    assert [row.state for row in found] == ["none", "instance"]
    assert node_types(found) == {
        "macro-daily-bias.bias": "none",
        "macro-daily-bias.summarize": "compensable",
    }
    assert len(rows(found)) == len(rows()) + 2


def test_an_operation_the_app_does_not_declare_is_no_row_and_no_order_act_is_one() -> None:
    assert app_rows("macro-daily-bias", "1.0.0", {}) == ()
    with pytest.raises(CatalogError, match="names the order act submit_order"):
        app_rows("macro-daily-bias", "1.0.0", {"place_order": {"approval": "manage"}})
    with pytest.raises(CatalogError, match="is longer than 64 characters"):
        app_rows("macro-daily-bias", "1.0.0", {"b" * 60: {}})
    assert check(app_rows("macro-daily-bias", "1.0.0", OPERATIONS)) is None


def test_a_ring_of_asks_is_bounded_by_the_host_setting_and_a_core_row_is_not() -> None:
    app = app_rows("macro-daily-bias", "1.0.0", OPERATIONS)[0]
    core = next(row for row in rows() if row.name == "library_get")
    assert dispatch_refusal(app, depth=0, ceiling=None) is None
    assert dispatch_refusal(app, depth=3, ceiling=2) == (
        "macro-daily-bias.bias is asked at depth 3, past the host's call_depth 2; the ring ends "
        "here"
    )
    assert dispatch_refusal(core, depth=9, ceiling=1) is None
    assert dispatch_refusal(app, depth=-1, ceiling=1) == "an ask's depth is never negative"
