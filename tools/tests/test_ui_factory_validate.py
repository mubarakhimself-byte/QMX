"""UI factory input validation: no-story waiting and missing fields."""

from __future__ import annotations

from pathlib import Path

from ui_factory.config import FactoryConfig
from ui_factory.story_parse import parse_epic_markdown
from ui_factory.validate_inputs import validate_inputs


def _cfg(root: Path) -> FactoryConfig:
    return FactoryConfig(
        destination_branch="ui-integration",
        backend_branch="integration",
        repo_root=root,
        state_dir=root / "state",
        worktree_root=root / "wts",
        epic_globs=("_bmad-output/planning-artifacts/epics-UI*.md",),
        python_quality={},
        host_app_roots=("apps/host",),
        shared_serial_paths=("pnpm-lock.yaml",),
        max_parallel_epics=2,
        max_repair_rounds=3,
        ci_timeout_seconds=30,
        product_host="apps/qmx-ui",
        fixture_host="tools/ui_factory/fixtures/factory-test-app",
        required_ci_checks=("Skylos", "QA Battery", "UI quality"),
    )


def test_no_story_files_wait_without_generating(tmp_path: Path) -> None:
    report = validate_inputs(_cfg(tmp_path))
    assert report.status == "waiting_for_input"
    assert report.generate_stories is False
    assert report.stories == 0
    assert any("do not generate" in w.lower() or "Supply BMAD" in w for w in report.waiting)


def test_empty_epic_file_waits(tmp_path: Path) -> None:
    folder = tmp_path / "_bmad-output" / "planning-artifacts"
    folder.mkdir(parents=True)
    (folder / "epics-UI-2026.md").write_text("# No stories yet\n", encoding="utf-8")
    report = validate_inputs(_cfg(tmp_path))
    assert report.status == "waiting_for_input"
    assert report.generate_stories is False


def test_missing_fields_are_named(tmp_path: Path) -> None:
    folder = tmp_path / "_bmad-output" / "planning-artifacts"
    folder.mkdir(parents=True)
    (folder / "epics-UI-2026.md").write_text(
        """### Epic 99: Shell (Wave 1, H)

### Story 99.1: Incomplete

As an operator I want chrome.
""",
        encoding="utf-8",
    )
    report = validate_inputs(_cfg(tmp_path))
    fields = {i.field for i in report.issues}
    assert "acceptance_criteria" in fields
    assert "source_documents" in fields
    assert "components" in fields
    assert "design_refs" in fields


def test_complete_story_parses_gwt(tmp_path: Path) -> None:
    path = tmp_path / "epics-UI.md"
    path.write_text(
        """### Epic 70: Host chrome (Wave 1, H)
**Feature:** FEAT-0064
**Notes:** Blocked by FEAT-0058
**Components:** COMP-QMA-WIRE

### Story 70.1: Rail destinations stay independent
As an operator,
I want Home and Copilot on the rail,
So that they are not the same destination.

**Traceability:** DEC-0470, ADR-0026, docs/lenses/ui/screens/home.md
**Acceptance Criteria:**

**Given** a cold start
**When** I open the shell
**Then** Home and Copilot are independent destinations
**And** WidgetFrame expand is not a fifth rail item

**Design:** docs/lenses/ui/design-system.md, docs/lenses/ui/screens/home.md
**Files:** apps/host/src/routes
**User-facing:** yes
""",
        encoding="utf-8",
    )
    epics = parse_epic_markdown(path)
    assert epics[0].id == "70"
    story = epics[0].stories[0]
    assert story.id == "70.1"
    assert story.acceptance_criteria
    assert "DEC-0470" in story.source_documents
    assert "docs/lenses/ui/design-system.md" in story.design_refs
    assert story.user_facing is True
