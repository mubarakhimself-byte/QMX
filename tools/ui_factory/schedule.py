"""Select UI epics. Shared files force sequential runs."""

from __future__ import annotations

from dataclasses import dataclass

from ui_factory.story_parse import EpicRecord

SHARED_HINTS = (
    "pnpm-lock.yaml",
    "package.json",
    "tokens.css",
    "components/ui",
)


@dataclass(frozen=True)
class PlannedEpic:
    epic_id: str
    title: str
    weight: str
    stories: tuple[str, ...]
    files: tuple[str, ...]
    disjoint: bool


def _files_for(epic: EpicRecord) -> set[str]:
    files: set[str] = set()
    for story in epic.stories:
        files.update(story.files)
        files.update(story.components)
    return files


def _shares(a: set[str], b: set[str]) -> bool:
    if not a or not b:
        return True
    if a & b:
        return True
    blob_a = " ".join(a).lower()
    blob_b = " ".join(b).lower()
    return any(hint in blob_a and hint in blob_b for hint in SHARED_HINTS)


def plan_epics(
    epics: list[EpicRecord],
    *,
    selected: set[str] | None,
    max_parallel: int,
) -> list[PlannedEpic]:
    chosen = [
        e
        for e in epics
        if selected is None or e.id in selected or any(s.id in selected for s in e.stories)
    ]
    planned: list[PlannedEpic] = []
    for epic in chosen:
        files = _files_for(epic)
        planned.append(
            PlannedEpic(
                epic_id=epic.id,
                title=epic.title,
                weight=epic.weight or "H",
                stories=tuple(s.id for s in epic.stories),
                files=tuple(sorted(files)),
                disjoint=True,
            )
        )
    if max_parallel < 2 or len(planned) < 2:
        return planned
    first_files = set(planned[0].files)
    second_files = set(planned[1].files)
    if _shares(first_files, second_files):
        planned[1] = PlannedEpic(
            epic_id=planned[1].epic_id,
            title=planned[1].title,
            weight=planned[1].weight,
            stories=planned[1].stories,
            files=planned[1].files,
            disjoint=False,
        )
    return planned


def build_model_for_weight(weight: str) -> str:
    if weight.upper() == "L":
        return "grok-4.5"
    return "grok-4.6"
