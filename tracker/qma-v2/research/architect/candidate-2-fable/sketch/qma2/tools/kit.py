"""The OpenAI engine's baseline tool kit: Claude's names, Claude's argument shapes, so hook
matchers and permission rules are written once (BASELINE 2.3).

Every handler is pure over (input, CallContext). The gate wrapper (registry.to_openai_tools)
runs before any of them; nothing here checks permissions.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from qma2.tools.registry import CallContext, ToolSpec


class BashInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    command: str
    timeout: int | None = None  # ms, as Claude
    description: str | None = None


class ReadInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_path: str
    offset: int | None = None
    limit: int | None = None


class WriteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_path: str
    content: str


class EditInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_path: str
    old_string: str
    new_string: str
    replace_all: bool = False


class GlobInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pattern: str
    path: str | None = None


class GrepInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pattern: str
    path: str | None = None
    glob: str | None = None
    output_mode: str = "files_with_matches"


class WebFetchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str
    prompt: str


class WebSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str


class TodoWriteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    todos: list[dict[str, str]]


class AskUserQuestionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    questions: list[dict[str, object]]


class AgentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str
    prompt: str
    subagent_type: str | None = None
    model: str | None = None
    run_in_background: bool = False


class SkillInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skill: str
    args: str | None = None


class ApplyPatchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patch: str  # Codex apply_patch grammar; GPT models are trained on it


async def bash(inp: BashInput, ctx: CallContext) -> str:
    """PowerShell on Windows, bash elsewhere, via ctx.run (supervisor: tree, timeout, cap)."""
    raise NotImplementedError


async def read(inp: ReadInput, ctx: CallContext) -> str: ...
async def write(inp: WriteInput, ctx: CallContext) -> str: ...
async def edit(inp: EditInput, ctx: CallContext) -> str: ...
async def glob(inp: GlobInput, ctx: CallContext) -> str: ...
async def grep(inp: GrepInput, ctx: CallContext) -> str:
    """ripgrep if present, else a Python fallback."""
    raise NotImplementedError


async def web_fetch(inp: WebFetchInput, ctx: CallContext) -> str:
    """httpx + markdownify; 10 MB cap; returns extracted text (the prompt is applied by the model)."""
    raise NotImplementedError


async def web_search(inp: WebSearchInput, ctx: CallContext) -> str:
    """Backend chosen by settings: hosted (OpenAI Responses) when available; else a QMX
    search provider. UNVERIFIED which free backend; the console shows "no search backend"."""
    raise NotImplementedError


async def todo_write(inp: TodoWriteInput, ctx: CallContext) -> str: ...
async def ask_user(inp: AskUserQuestionInput, ctx: CallContext) -> str:
    """ctx.ask(ApprovalRequest(kind="question", ...)) — same broker, same operator proof."""
    raise NotImplementedError


async def agent(inp: AgentInput, ctx: CallContext) -> str:
    """Implemented in engines/openai.py (needs the Runner); registered here for the name,
    depth (3) and concurrency (6) limits. Background: asyncio task + SendMessage/wait/list."""
    raise NotImplementedError


async def skill(inp: SkillInput, ctx: CallContext) -> str:
    """Return the SKILL.md body from the skills dirs; capped at 5,000 tokens as Claude does."""
    raise NotImplementedError


async def apply_patch(inp: ApplyPatchInput, ctx: CallContext) -> str: ...


def baseline_specs(cwd: Path, *, gpt_family: bool) -> Sequence[ToolSpec]:
    """The kit for one OpenAI-engine segment. `apply_patch` only for GPT models."""
    raise NotImplementedError
