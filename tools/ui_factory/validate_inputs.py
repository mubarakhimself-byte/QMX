"""Validate supplied UI stories. Missing stories is waiting, not generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ui_factory.config import FactoryConfig
from ui_factory.story_parse import (
    EpicRecord,
    StoryRecord,
    discover_epic_files,
    parse_epic_markdown,
)

BACKEND_COMPONENTS = {
    "COMP-QMA-DAEMON",
    "COMP-QMB",
    "COMP-QMA-CORE",
    "qma-daemon",
    "qmb",
}
UI_DESIGN_HINTS = (
    "docs/lenses/ui",
    "ADR-0026",
    "design-system",
    "SCN-0028",
    "SCN-0034",
    "WidgetFrame",
)


@dataclass
class FieldIssue:
    story_id: str
    field: str
    message: str


@dataclass
class ValidateReport:
    status: str
    epic_files: list[str]
    epics: int
    stories: int
    issues: list[FieldIssue] = field(default_factory=list)
    waiting: list[str] = field(default_factory=list)
    runnable: list[str] = field(default_factory=list)
    generate_stories: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["issues"] = [asdict(i) for i in self.issues]
        return payload


def _story_issues(story: StoryRecord) -> list[FieldIssue]:
    issues: list[FieldIssue] = []
    if story.id == "":
        issues.append(FieldIssue(story.id, "id", "story id missing"))
    if story.title == "":
        issues.append(FieldIssue(story.id, "title", "title missing"))
    if story.brief == "":
        issues.append(
            FieldIssue(story.id, "brief", "user-story brief missing")
        )
    if not story.acceptance_criteria:
        issues.append(
            FieldIssue(
                story.id,
                "acceptance_criteria",
                "no Given/When/Then acceptance criteria",
            )
        )
    if not story.source_documents:
        issues.append(
            FieldIssue(
                story.id,
                "source_documents",
                "Traceability / source documents missing",
            )
        )
    if not story.components:
        issues.append(
            FieldIssue(
                story.id,
                "components",
                "touched components missing",
            )
        )
    if not story.design_refs:
        hinted = any(
            hint.lower() in story.brief.lower()
            or any(hint.lower() in ac.lower() for ac in story.acceptance_criteria)
            for hint in UI_DESIGN_HINTS
        )
        if not hinted:
            issues.append(
                FieldIssue(
                    story.id,
                    "design_refs",
                    "design / UI lens references missing",
                )
            )
    if story.depends_on is None:
        issues.append(
            FieldIssue(story.id, "depends_on", "dependency edges missing")
        )
    return issues


def _needs_backend(story: StoryRecord) -> bool:
    names = {c.upper() for c in story.components}
    if names & {c.upper() for c in BACKEND_COMPONENTS}:
        return True
    joined = " ".join(story.depends_on).upper()
    return "FEAT-0041" in joined or "FEAT-0042" in joined or "FEAT-0065" in joined


def load_epics(config: FactoryConfig) -> list[EpicRecord]:
    files = discover_epic_files(config.repo_root, config.epic_globs)
    epics: list[EpicRecord] = []
    for path in files:
        epics.extend(parse_epic_markdown(path))
    return epics


def validate_inputs(
    config: FactoryConfig,
    *,
    selected: set[str] | None = None,
    merged_features: set[str] | None = None,
) -> ValidateReport:
    files = discover_epic_files(config.repo_root, config.epic_globs)
    if not files:
        return ValidateReport(
            status="waiting_for_input",
            epic_files=[],
            epics=0,
            stories=0,
            waiting=[
                "No UI epic files matched "
                + ", ".join(config.epic_globs)
                + ". Supply BMAD epics/stories; do not generate a backlog."
            ],
            generate_stories=False,
        )
    epics = []
    for path in files:
        epics.extend(parse_epic_markdown(path))
    stories = [s for e in epics for s in e.stories]
    if selected:
        stories = [s for s in stories if s.id in selected or s.epic_id in selected]
    if not stories:
        return ValidateReport(
            status="waiting_for_input",
            epic_files=[str(p) for p in files],
            epics=len(epics),
            stories=0,
            waiting=[
                "Epic files exist but contain no stories. "
                "Waiting for BMAD-created stories."
            ],
            generate_stories=False,
        )
    issues: list[FieldIssue] = []
    waiting: list[str] = []
    runnable: list[str] = []
    known = merged_features or set()
    for story in stories:
        issues.extend(_story_issues(story))
        blocked = [
            dep
            for dep in story.depends_on
            if dep.startswith("FEAT-") and dep not in known
        ]
        backend_wait = _needs_backend(story) and bool(blocked)
        missing_required = any(
            i.field in {"acceptance_criteria", "id", "title"} for i in issues
            if i.story_id == story.id
        )
        if missing_required:
            waiting.append(f"{story.id} blocked on missing required fields")
        elif backend_wait:
            waiting.append(
                f"{story.id} waits on unfinished backend: " + ", ".join(blocked)
            )
        else:
            runnable.append(story.id)
    status = "ready"
    if issues and not runnable:
        status = "invalid_input"
    elif waiting and runnable:
        status = "partial"
    elif waiting and not runnable:
        status = "waiting_for_backend"
    return ValidateReport(
        status=status,
        epic_files=[str(p) for p in files],
        epics=len(epics),
        stories=len(stories),
        issues=issues,
        waiting=waiting,
        runnable=runnable,
        generate_stories=False,
    )
