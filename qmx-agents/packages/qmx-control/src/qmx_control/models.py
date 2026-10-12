"""Shared documents and transport-independent errors."""

from pydantic import BaseModel, ConfigDict, Field, JsonValue

type Document = dict[str, JsonValue]


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
