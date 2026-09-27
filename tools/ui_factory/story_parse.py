"""Parse BMAD epic/story markdown into machine records.

Does not invent stories. Missing fields stay missing so validate-inputs
can report them precisely.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

STORY_HEAD = re.compile(r"^### Story ([0-9]+(?:\.[0-9]+)+):\s*(.+)\s*$")
EPIC_HEAD = re.compile(
    r"^### Epic ([0-9]+):\s*(.+?)(?:\s*\((?:Wave\s+[^,]+,\s*)?([HLM])\))?\s*$"
)


@dataclass
class StoryRecord:
    id: str
    title: str
    epic_id: str
    brief: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    source_documents: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    design_refs: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    user_facing: bool | None = None
    feature: str = ""
    weight: str = ""
    source_path: str = ""
    line: int = 0

    def story_hash_material(self) -> str:
        ac = "\n".join(self.acceptance_criteria)
        deps = ",".join(self.depends_on)
        return f"{self.id}|{self.title}|{self.brief}|{ac}|{deps}"


@dataclass
class EpicRecord:
    id: str
    title: str
    weight: str
    feature: str
    notes: str
    stories: list[StoryRecord]
    source_path: str
    depends_on: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)


def _split_csv(text: str) -> list[str]:
    parts: list[str] = []
    for chunk in re.split(r"[,;]", text):
        item = chunk.strip().strip(".*").strip()
        if item:
            parts.append(item)
    return parts


def _after_label(line: str) -> str:
    if ":**" in line:
        return line.split(":**", 1)[1].strip()
    if ":" in line:
        return line.split(":", 1)[1].strip()
    return ""


def parse_epic_markdown(path: Path) -> list[EpicRecord]:
    lines = path.read_text(encoding="utf-8").splitlines()
    epics: list[EpicRecord] = []
    current: EpicRecord | None = None
    story: StoryRecord | None = None
    section = ""
    brief_lines: list[str] = []

    def flush_story() -> None:
        nonlocal story, brief_lines
        if current is None or story is None:
            return
        if story.brief == "" and brief_lines:
            story.brief = "\n".join(brief_lines).strip()
        if not story.components:
            story.components = list(current.components)
        if not story.depends_on:
            story.depends_on = list(current.depends_on)
        if story.feature == "":
            story.feature = current.feature
        if story.weight == "":
            story.weight = current.weight
        current.stories.append(story)
        story = None
        brief_lines = []

    for index, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        epic_match = EPIC_HEAD.match(line)
        if epic_match:
            flush_story()
            if current is not None:
                epics.append(current)
            current = EpicRecord(
                id=epic_match.group(1),
                title=epic_match.group(2).strip(),
                weight=(epic_match.group(3) or "").upper(),
                feature="",
                notes="",
                stories=[],
                source_path=str(path),
            )
            section = "epic-intro"
            continue
        story_match = STORY_HEAD.match(line)
        if story_match and current is not None:
            flush_story()
            story = StoryRecord(
                id=story_match.group(1),
                title=story_match.group(2).strip(),
                epic_id=current.id,
                source_path=str(path),
                line=index,
            )
            section = "story-brief"
            brief_lines = []
            continue
        if current is None:
            continue
        stripped = line.strip()
        if stripped.startswith("**Feature:**"):
            current.feature = _after_label(stripped)
            continue
        if stripped.startswith("**Notes:**"):
            current.notes = _after_label(stripped)
            if "Blocked by" in current.notes or "blocked by" in current.notes:
                current.depends_on.extend(
                    re.findall(r"FEAT-[0-9]+", current.notes)
                )
            continue
        if story is None:
            if stripped.startswith("**Components:**") or stripped.startswith(
                "**Touched:**"
            ):
                current.components.extend(_split_csv(_after_label(stripped)))
            continue
        if stripped.startswith("**Traceability:**"):
            story.source_documents.extend(_split_csv(_after_label(stripped)))
            section = "trace"
            continue
        if stripped.startswith("**Acceptance Criteria:**"):
            section = "ac"
            continue
        if stripped.startswith("**Components:**") or stripped.startswith(
            "**Touched:**"
        ):
            story.components.extend(_split_csv(_after_label(stripped)))
            continue
        if stripped.startswith("**Design:**") or stripped.startswith("**UI lens:**"):
            story.design_refs.extend(_split_csv(_after_label(stripped)))
            continue
        if stripped.startswith("**Needs:**") or stripped.startswith("**Blocked by:**"):
            rest = _after_label(stripped)
            story.depends_on.extend(_split_csv(rest))
            story.depends_on.extend(re.findall(r"FEAT-[0-9]+", stripped))
            continue
        if stripped.startswith("**Files:**"):
            story.files.extend(_split_csv(_after_label(stripped)))
            continue
        if stripped.startswith("**User-facing:**"):
            flag = _after_label(stripped).lower()
            story.user_facing = flag in {"yes", "true", "1"}
            continue
        if section == "ac" and stripped.startswith("**Given**"):
            story.acceptance_criteria.append(stripped)
            continue
        if section == "ac" and (
            stripped.startswith("**When**")
            or stripped.startswith("**Then**")
            or stripped.startswith("**And**")
        ):
            if story.acceptance_criteria:
                story.acceptance_criteria[-1] += " " + stripped
            else:
                story.acceptance_criteria.append(stripped)
            continue
        if section == "story-brief" and stripped and not stripped.startswith("#"):
            brief_lines.append(stripped)

    flush_story()
    if current is not None:
        epics.append(current)
    return epics


def discover_epic_files(repo_root: Path, globs: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    for pattern in globs:
        found.extend(sorted(repo_root.glob(pattern)))
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in found:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique
