"""The vendored order-word list and the one function that reads it (engine AD-54, review 48 M10).

Copied from `qma.core.barriers.money_path` so nothing here imports `qma.core`. Hygiene, not a
boundary: agents have no path to money (ruling 116). Three users read it through
`named_money_act`: the engine's definition lint, the vetting of an external MCP server's tool
list, and the unit test that no QMX operation names an order act.
"""

from __future__ import annotations

import re
from typing import Final

ACT_FAMILIES: Final = frozenset(
    {
        "order", "position", "protection", "sizing", "binding", "mode", "control",
        "zone_transition", "promotion",
    }
)  # fmt: skip
DENIED_ACTS: Final = frozenset(
    {
        "submit_order", "amend_order", "cancel_order", "replace_order", "open_position",
        "close_position", "reduce_position", "hedge_position", "set_protection",
        "amend_protection", "size", "resize", "mint_sizing_decision", "create_binding",
        "amend_binding", "activate_binding", "stand_down_binding", "delete_binding",
        "set_book_mode", "set_seat_state", "set_book_parameter", "set_bms_parameter",
        "set_priority_rank", "set_capital_floor", "arm_kill_switch", "disarm_kill_switch",
        "change_kill_switch", "change_control_action",
    }
)  # fmt: skip
ALIASES: Final = {
    "create_order": "submit_order",
    "place_order": "submit_order",
    "place_an_order": "submit_order",
    "submit_an_order": "submit_order",
    "order_submit": "submit_order",
    "amend_an_order": "amend_order",
    "order_amend": "amend_order",
    "cancel_an_order": "cancel_order",
    "order_cancel": "cancel_order",
    "replace_an_order": "replace_order",
    "order_replace": "replace_order",
    "close_by": "close_position",
    "open_a_position": "open_position",
    "close_a_position": "close_position",
    "reduce_a_position": "reduce_position",
    "hedge_a_position": "hedge_position",
    "set_a_protection": "set_protection",
    "amend_a_protection": "amend_protection",
    "re_size": "resize",
    "re_size_sizing": "resize",
    "mint_a_sizing_decision": "mint_sizing_decision",
    "sizing_decision": "mint_sizing_decision",
    "create_a_binding": "create_binding",
    "quant_to_book_binding": "create_binding",
    "bot_to_book_binding": "create_binding",
    "stand_down": "stand_down_binding",
    "book_mode": "set_book_mode",
    "seat_state": "set_seat_state",
    "book_parameter": "set_book_parameter",
    "bms_parameter": "set_bms_parameter",
    "priority_rank": "set_priority_rank",
    "capital_floor": "set_capital_floor",
    "kill_switch": "change_kill_switch",
    "node_control_action": "change_control_action",
    "control_action": "change_control_action",
    "transition_zone": "zone_transition",
    "transition_a_registry_artifact": "zone_transition",
    "promote": "promotion",
}
ROLE_PREFIXES: Final = ("paper_only_", "live_only_", "demo_only_", "paper_", "live_", "demo_")
"""Longest first. Paper is an account role on a real venue, not a sandbox."""
COMPOUND_NOUNS: Final = {
    ("stop", "loss"): "stop_loss",
    ("take", "profit"): "take_profit",
    ("trailing", "stop"): "trailing_stop",
    ("trading", "stop"): "trading_stop",
    ("money", "path"): "money_path",
}
PROTECTION_NOUNS: Final = frozenset(
    {
        "stop_loss", "take_profit", "trailing_stop", "trading_stop", "sltp", "tpsl", "sl", "tp",
        "stoploss", "takeprofit", "breakeven",
    }
)  # fmt: skip
FAMILY_NOUNS: Final = frozenset({"order", "position", "trade", "oco", "oso", "oto"}) | (
    PROTECTION_NOUNS
)
NON_MONEY_OBJECTS: Final = frozenset({"journal", "note", "watchlist"})
MUTATING_VERBS: Final = frozenset(
    {
        "send", "close", "cancel", "exit", "execute", "amend", "replace", "submit", "new",
        "create", "place", "modify", "reduce", "hedge", "flatten", "open", "add", "update",
        "edit", "change", "delete", "remove", "enter", "increase", "decrease", "reverse", "flip",
        "move", "set", "adjust", "switch", "exercise", "scale", "stop", "go", "put", "post",
        "make", "upsert", "patch", "convert", "attach", "detach", "trail", "arm", "disarm",
        "activate", "deactivate", "enable", "disable", "toggle", "reset", "clear", "drop",
        "halt", "resume", "pause", "start", "trigger", "fire", "roll", "rollover",
        "unwind", "settle", "assign", "allocate", "release", "approve", "confirm", "accept",
        "reject", "revoke", "write", "save", "apply", "register", "configure", "override",
    }
)  # fmt: skip
MONEY_VERBS: Final = frozenset(
    {
        "buy", "sell", "withdraw", "transfer", "liquidate", "deposit", "pay", "swap", "borrow",
        "repay", "stake", "unstake",
    }
)  # fmt: skip
"""Verbs that move money by themselves, with no family noun."""

_CAMEL: Final = re.compile(r"([a-z0-9])([A-Z])")


def listed_act(text: str) -> str | None:
    """The act family or enumerated act `text` spells exactly, aliases and role prefixes
    folded (`paper_place_order` is `submit_order`)."""
    token = "_".join(text.strip().casefold().replace("-", "_").replace("/", "_").split())
    token = re.sub(r"_+", "_", token).strip("_")
    for prefix in ROLE_PREFIXES:
        if token.startswith(prefix) and len(token) > len(prefix):
            token = token.removeprefix(prefix)
            break
    token = ALIASES.get(token, token)
    return token if token in ACT_FAMILIES | DENIED_ACTS else None


def word_act(text: str) -> str | None:
    """An identifier (no spaces) holding a money verb (`paper_buy`), or a mutating verb with an
    order, position or protection noun (`closeAllPositions`, `update_stop_loss`). Prose is left
    alone so a prompt can talk about markets."""
    if re.search(r"\s", text.strip()):
        return None
    raw = [w for w in re.split(r"[^a-z0-9]+", _CAMEL.sub(r"\1_\2", text).casefold()) if w]
    words: list[str] = []
    for word in raw:
        if words and (compound := COMPOUND_NOUNS.get((words[-1], word))):
            words[-1] = compound
        else:
            singular = word.removesuffix("s")
            words.append(singular if singular in FAMILY_NOUNS else word)
    if money := next((w for w in words if w in MONEY_VERBS), None):
        return money
    verb = next((w for w in words if w in MUTATING_VERBS), None)
    noun = next((w for w in words if w in FAMILY_NOUNS), None)
    if verb and noun and not NON_MONEY_OBJECTS & set(words):
        return f"{verb}_{noun}"
    return None


def named_money_act(text: str) -> str | None:
    """The money act a name spells, or None: `listed_act`, then `word_act`."""
    return listed_act(text) or word_act(text)
