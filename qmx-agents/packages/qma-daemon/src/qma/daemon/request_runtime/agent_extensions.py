"""Host scope/provenance glue for released SDK skills and trusted middleware.

No skill parser, dynamic import, plugin installer or document-code execution.
Local input is snapshotted before SDK discovery; the model never selects roots.
"""

from __future__ import annotations

import hashlib
import re
import stat
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from importlib.metadata import version
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import yaml

from .contracts import ProviderEvent

if TYPE_CHECKING:
    from langchain.agents.middleware import AgentMiddleware

MAX_FILE_BYTES = 16_384
MAX_LIBRARY_BYTES = 65_536
MAX_FILES = 64
MAX_SKILLS = 16
MAX_YAML_EVENTS = 256
MAX_YAML_DEPTH = 16


@dataclass(frozen=True)
class MiddlewareBinding:
    """Trusted registered code. Config selects an id; never Python/script text."""

    name: str
    version: str
    factory: Callable[[Callable[[ProviderEvent], None]], AgentMiddleware[Any, Any, Any]]


@dataclass(frozen=True)
class LibraryProfile:
    profile_id: str
    sources: tuple[str, ...]
    sessions: tuple[str, ...] | None
    workflows: tuple[str, ...]
    middleware: tuple[str, ...]


@dataclass(frozen=True)
class ExtensionSelection:
    files: tuple[tuple[str, str], ...]
    sources: tuple[str, ...]
    middleware: tuple[MiddlewareBinding, ...]

    def binding(self) -> dict[str, object]:
        return {
            "revision": "sdk-skills-1",
            "sdk_versions": {
                name: version(name)
                for name in (
                    "langchain",
                    "langgraph",
                    "deepagents",
                    "PyYAML",
                )
            },
            "sources": list(self.sources),
            "files": {
                path: hashlib.sha256(content.encode("utf-8")).hexdigest()
                for path, content in self.files
            },
            "middleware": [[item.name, item.version] for item in self.middleware],
        }


@dataclass(frozen=True)
class AgentExtensions:
    files: tuple[tuple[str, str], ...] = ()
    profiles: tuple[LibraryProfile, ...] = ()
    registered: tuple[MiddlewareBinding, ...] = ()

    def select(self, profile: str, session: str, workflow: str) -> ExtensionSelection:
        selected = next((item for item in self.profiles if item.profile_id == profile), None)
        if (
            selected is None
            or workflow not in selected.workflows
            or (selected.sessions is not None and session not in selected.sessions)
        ):
            return ExtensionSelection((), (), ())
        sources = tuple(f"/skills/{name}/" for name in selected.sources)
        return ExtensionSelection(
            tuple((path, body) for path, body in self.files if path.startswith(sources)),
            sources,
            tuple(
                next(item for item in self.registered if item.name == name)
                for name in selected.middleware
            ),
        )

    def manifest(self) -> dict[str, object]:
        """Nonsecret host identity, including all scope associations and content pins."""
        return {
            "snapshot": ExtensionSelection(self.files, (), self.registered).binding(),
            "profiles": [
                {
                    "id": item.profile_id,
                    "sources": list(item.sources),
                    "sessions": list(item.sessions) if item.sessions is not None else [],
                    "all_profile_sessions": item.sessions is None,
                    "workflows": list(item.workflows),
                    "middleware": list(item.middleware),
                }
                for item in self.profiles
            ],
        }


def _object(value: object, keys: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("extension configuration requires objects")
    raw = cast("dict[object, object]", value)
    if any(not isinstance(key, str) for key in raw):
        raise ValueError("extension configuration requires objects")
    if keys is not None and set(raw) - keys:
        raise ValueError("unsupported extension configuration field")
    return cast("dict[str, Any]", raw)


def _names(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError("bounded unique extension names required")
    raw = cast("list[object]", value)
    if (
        len(raw) > 32
        or any(not isinstance(item, str) or not item.strip() or len(item) > 128 for item in raw)
        or len(raw) != len(set(raw))
    ):
        raise ValueError("bounded unique extension names required")
    return tuple(cast("list[str]", raw))


def _plain(path: Path) -> None:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError("skill input cannot use links or reparse points")


def _bounded_frontmatter(content: str) -> None:
    """Admission complexity check only; SDK owns skill parsing and metadata.

    Safe loading alone does not bound alias expansion when the SDK coerces
    metadata values to strings. Reuse PyYAML's streaming events without constructing
    YAML objects. Match the released SDK delimiter syntax; unsupported aliases,
    anchors, deep nesting, event overflow and malformed syntax refuse startup.
    """
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if match is None:
        return
    depth = 0
    parse_events = cast("Callable[[str], Iterable[Any]]", yaml.parse)  # pyright: ignore[reportUnknownMemberType] - upstream untyped stream API
    try:
        for count, event in enumerate(parse_events(match.group(1)), 1):
            if (
                count > MAX_YAML_EVENTS
                or isinstance(event, yaml.AliasEvent)
                or getattr(event, "anchor", None) is not None
            ):
                raise ValueError("skill YAML complexity budget exceeded")
            if isinstance(event, (yaml.MappingStartEvent, yaml.SequenceStartEvent)):
                depth += 1
            elif isinstance(event, (yaml.MappingEndEvent, yaml.SequenceEndEvent)):
                depth -= 1
            if depth > MAX_YAML_DEPTH:
                raise ValueError("skill YAML depth budget exceeded")
    except yaml.YAMLError as exc:
        raise ValueError("invalid skill YAML syntax") from exc


def load_agent_extensions(
    root: Path,
    value: object,
    *,
    registered: tuple[MiddlewareBinding, ...] | None = None,
) -> AgentExtensions:
    """Bound host-approved files; leave SKILL.md parsing/discovery to Deep Agents.

    The config root and declared paths are trusted operator input. Only immediate
    skill folders and one level of text references are ingested. No scripts/assets.
    Host-controlled immutable storage is required against concurrent file swapping;
    this snapshot importer is not an OS sandbox.
    """
    from .sdk_middleware import audit_binding  # noqa: PLC0415 - avoids module cycle

    config = _object(value, {"roots", "profiles"})
    registrations = registered if registered is not None else (audit_binding(),)
    if len({item.name for item in registrations}) != len(registrations):
        raise ValueError("duplicate trusted middleware id")
    roots = _object(config.get("roots", {}))
    if len(roots) > 4:
        raise ValueError("too many skill roots")
    base = root.resolve(strict=True)
    files: list[tuple[str, str]] = []
    total = 0
    skills = 0
    for alias, relative in sorted(roots.items()):
        if re.fullmatch(r"[a-z][a-z0-9-]{0,31}", alias) is None or (
            not isinstance(relative, str)
            or not relative
            or Path(relative).anchor
            or ":" in relative
            or any(part in {"..", "."} for part in Path(relative).parts)
        ):
            raise ValueError("relative allowlisted skill roots required")
        declared = base / relative
        if not declared.is_relative_to(base) or declared == base:
            raise ValueError("skill root is outside host scope")
        _plain(declared)
        for parent in declared.parents:
            if parent == base:
                break
            _plain(parent)
        resolved = declared.resolve(strict=True)
        if not resolved.is_relative_to(base) or resolved == base or not resolved.is_dir():
            raise ValueError("skill root is outside host scope")
        children = list(islice(resolved.iterdir(), MAX_SKILLS + 1))
        if len(children) > MAX_SKILLS:
            raise ValueError("skill root entry budget exceeded")
        for directory in sorted(children):
            _plain(directory)
            if not directory.is_dir():
                continue
            skill = directory / "SKILL.md"
            if not skill.exists():
                continue
            skills += 1
            if skills > MAX_SKILLS:
                raise ValueError("skill count budget exceeded")
            candidates = [skill]
            references = directory / "references"
            if references.exists():
                _plain(references)
                references_list = list(islice(references.iterdir(), MAX_FILES + 1))
                if len(references_list) > MAX_FILES:
                    raise ValueError("reference count budget exceeded")
                candidates.extend(references_list)
            for path in sorted(candidates):
                _plain(path)
                if not stat.S_ISREG(path.stat().st_mode) or path.suffix.lower() not in {
                    ".md",
                    ".txt",
                    ".json",
                    ".yaml",
                    ".yml",
                }:
                    raise ValueError("skill resources must be regular text files")
                with path.open("rb") as source:
                    content = source.read(MAX_FILE_BYTES + 1)
                total += len(content)
                if len(content) > MAX_FILE_BYTES or total > MAX_LIBRARY_BYTES:
                    raise ValueError("skill byte budget exceeded")
                decoded = content.decode("utf-8")
                if path.name == "SKILL.md":
                    _bounded_frontmatter(decoded)
                files.append(
                    (
                        f"/skills/{alias}/{path.relative_to(resolved).as_posix()}",
                        decoded,
                    )
                )
                if len(files) > MAX_FILES:
                    raise ValueError("skill resource count budget exceeded")
    profiles = _object(config.get("profiles", {}))
    if len(profiles) > 32:
        raise ValueError("too many extension profiles")
    selections: list[LibraryProfile] = []
    for profile, raw in sorted(profiles.items()):
        _names([profile])
        row = _object(raw, {"sources", "sessions", "workflows", "middleware"})
        sources = _names(row.get("sources", []))
        middleware = _names(row.get("middleware", []))
        if set(sources) - set(roots) or set(middleware) - {item.name for item in registrations}:
            raise ValueError("unknown host source or registered middleware")
        selections.append(
            LibraryProfile(
                profile,
                sources,
                _names(row["sessions"]) if "sessions" in row else None,
                _names(row.get("workflows", ["request"])),
                middleware,
            )
        )
    return AgentExtensions(tuple(files), tuple(selections), registrations)
