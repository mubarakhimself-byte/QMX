"""Shared documents and transport-independent errors."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

type Document = dict[str, JsonValue]

DELEGATE_SUMMARY_CHARS = 4_000
"""How much of a helper's answer one completion row keeps. The full text, when longer, is a
Library artifact the row points at (AD-41)."""


class DelegateCompletion(BaseModel):
    """One `delegate` helper's answer as the parent will be handed it (AD-41). Stored in
    `control.db` before it is announced or delivered, so a host restart loses nothing."""

    model_config = ConfigDict(extra="forbid")
    handle: str = Field(min_length=1, max_length=64)
    parent_session: str = Field(min_length=1)
    state: Literal["done", "failed", "stalled", "stopped"]
    summary: str = Field(default="", max_length=DELEGATE_SUMMARY_CHARS)
    artifact_id: str = ""
    """A Library artifact holding the full answer when `summary` was cut."""
    schema_valid: bool = True
    """False when an `output_schema` helper never produced a document that holds to it."""


class ControlError(Exception):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status

    def document(self) -> Document:
        return {"error": {"code": self.code, "message": str(self)}}


class LibraryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    kind: str = Field(min_length=1)
    content: JsonValue
    tags: list[str] = Field(default_factory=list)
    source: str = ""
    extracted_text: str = ""
    previous_id: str | None = None
    fetched_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class MemoKey(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy_version: str = Field(min_length=1)
    data_snapshot: str = Field(min_length=1)
    params: Document
    engine_version: str = Field(min_length=1)
