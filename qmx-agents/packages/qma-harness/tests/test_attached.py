"""The `attached` list on the chat record (H49, AD-63) and the excerpt budgets the Surface keeps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from qmx_control.context import AttachedRef
from qmx_router.ids import SessionId

from qma.harness.home import ChatRecord, QmxHome, read_record, write_record
from qma.harness.launch import ChatConfig, Home, Interactive
from qma.harness.profiles import PLAN
from qma.harness.surface import (
    CHARS_PER_TOKEN,
    EXCERPT_HARD,
    EXCERPT_SOFT,
    MAX_FOLDER_ENTRIES,
    excerpt_budget,
)
from qma.harness.tools import HOST_SCHEMAS

CHAT = SessionId("0b6f3e1c-3333-4c4c-9a9a-000000000003")


@pytest.fixture
def home(tmp_path: Path) -> QmxHome:
    return QmxHome(tmp_path / "qmx")


def record(home: QmxHome, attached: tuple[AttachedRef, ...] = ()) -> ChatRecord:
    config = ChatConfig(PLAN, "haiku", None, "default", home.root / "ws", Interactive())
    return ChatRecord(CHAT, config, started=False, turn="idle", attached=attached)


POD = AttachedRef("@pod:pod-7", "pod-7", version_id="fp1:sha256::pod7")
RUN = AttachedRef(
    "@run:0192/aa", "0192", pin="follow", artifact_id="fp1:sha256::bias", status="pending"
)


def test_the_attached_list_is_a_field_of_the_record_and_survives_a_reload(home: QmxHome) -> None:
    write_record(home, record(home, (POD, RUN)))

    found = read_record(home, CHAT)

    assert found is not None
    assert found.attached == (POD, RUN)
    document = json.loads((home.chats_dir / f"{CHAT}.json").read_text(encoding="utf-8"))
    assert document["attached"] == [
        {
            "ref": "@pod:pod-7",
            "item_id": "pod-7",
            "pin": "version",
            "version_id": "fp1:sha256::pod7",
            "artifact_id": None,
            "status": "ready",
            "note": "",
        },
        {
            "ref": "@run:0192/aa",
            "item_id": "0192",
            "pin": "follow",
            "version_id": None,
            "artifact_id": "fp1:sha256::bias",
            "status": "pending",
            "note": "",
        },
    ]


def test_a_record_written_before_the_field_reads_an_empty_list(home: QmxHome) -> None:
    path = home.chats_dir / f"{CHAT}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    document = json.loads(json.dumps({"started": True, "turn": "idle"}))
    document["session_id"] = CHAT
    document["config"] = {
        "profile": PLAN,
        "model": "haiku",
        "effort": None,
        "mode": "default",
        "workspace": str(home.root / "ws"),
        "kind": {"type": "interactive"},
        "home": {"kind": "lab", "project_id": "pod-7"},
    }
    path.write_text(json.dumps(document), encoding="utf-8")

    found = read_record(home, CHAT)

    assert found is not None
    assert found.attached == ()
    assert found.config.home == Home("lab", "pod-7")


def test_the_excerpt_budget_is_a_quarter_and_a_half_of_the_window() -> None:
    found = excerpt_budget({})

    assert (found.soft_chars, found.hard_chars) == (
        int(200_000 * CHARS_PER_TOKEN * EXCERPT_SOFT),
        int(200_000 * CHARS_PER_TOKEN * EXCERPT_HARD),
    )
    assert found.folder_entries == MAX_FOLDER_ENTRIES == 200
    assert found.soft_chars == 200_000
    assert found.hard_chars == 400_000


def test_a_written_excerpt_budget_wins_and_a_hard_share_never_goes_under_the_soft() -> None:
    found = excerpt_budget(
        {"excerpt": {"soft": 0.1, "hard": 0.05, "window_tokens": 1_000, "folder_entries": 25}}
    )
    whole = excerpt_budget({"excerpt": {"soft": 2, "hard": "half", "folder_entries": 0}})

    assert (found.soft_chars, found.hard_chars, found.folder_entries) == (400, 400, 25)
    assert (whole.soft_chars, whole.hard_chars) == (200_000, 400_000)
    assert whole.folder_entries == MAX_FOLDER_ENTRIES


def test_the_excerpt_budget_holds_its_three_numbers() -> None:
    found = excerpt_budget({"excerpt": {"window_tokens": 1_000}})

    assert (found.soft_chars, found.hard_chars, found.folder_entries) == (1_000, 2_000, 200)


def test_the_context_rows_carry_the_arguments_the_model_needs() -> None:
    add = dict(HOST_SCHEMAS["context_add"])
    properties = cast("dict[str, dict[str, object]]", add["properties"])

    assert properties["ref"]["type"] == "string"
    assert properties["pin"]["enum"] == ["version", "follow"]
    assert add["required"] == ["ref"]
    assert HOST_SCHEMAS["context_read"]["required"] == ["ref"]
