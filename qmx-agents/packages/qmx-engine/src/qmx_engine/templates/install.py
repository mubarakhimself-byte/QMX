"""Install the template pack disabled (ruling 83), idempotent by content hash.

A runnable template is saved as a draft, test-run on real models with its catalogue test inputs,
published (`0.1.0` the first time, the next patch after), and given its card's triggers, disabled.
A template whose definition names `meta.needs` is saved as a validated draft and goes no further.
A template whose content hash is already published, or a `needs` draft already saved with the same
files, is left as it is, so a second install changes nothing. Nothing is ever enabled here:
enabling is the operator's act (AD-22).
"""

from __future__ import annotations

import secrets
import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from qmx_engine.definition.validate import needs_line
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import Bundle, Draft, LibraryRefused
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Caller
from qmx_engine.templates.catalog import CATALOG, PACK, Template
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import stamp

type Action = Literal["published", "saved draft", "unchanged", "test failed", "invalid"]


@dataclass(frozen=True, slots=True)
class Installed:
    template: Template
    action: Action
    detail: str


async def install(
    svc: EngineService, templates: Iterable[Template] = CATALOG, *, caller: Caller = OPERATOR
) -> list[Installed]:
    return [await install_one(svc, template, caller) for template in templates]


def current_draft(svc: EngineService, item: str) -> Draft | None:
    try:
        return svc.drafts.get(item)
    except LibraryRefused:
        return None


async def install_one(svc: EngineService, template: Template, caller: Caller) -> Installed:
    item = template.folder
    bundle = Bundle.read(PACK / item)
    content_hash = bundle.content_hash()
    if any(v.content_hash == content_hash for v in svc.versions.list(item)):
        return Installed(template, "unchanged", f"{content_hash} is already published")
    draft = current_draft(svc, item)
    if draft is None or draft.bundle != bundle:
        revision = 0 if draft is None else draft.revision
        svc.drafts.put(item, bundle, revision, caller=caller)
    elif bundle.needs():
        return Installed(template, "unchanged", "the same draft is already saved")
    problems = svc.drafts.validate(item)
    if problems:
        codes = " ".join(sorted({p.code for p in problems}))
        return Installed(template, "invalid", f"the draft does not validate: {codes}")
    if bundle.needs():
        return Installed(template, "saved draft", needs_line(bundle.needs()))
    if svc.drafts.state(item) != "tested":
        started = time.monotonic()
        report = await svc.tests.run(item, caller=caller, inputs=template.test_inputs)
        cost = test_cost(svc, report.run_id, time.monotonic() - started)
        if report.status != "passed":
            return Installed(template, "test failed", f"run {report.run_id}: {report.reason}")
    else:
        cost = "tested earlier"
    taken = [v.semver for v in svc.versions.list(item)]
    semver = next_patch(taken)
    object_id = svc.versions.publish(item, semver, caller=caller)
    for spec in template.triggers:
        add_disabled_trigger(svc, item, object_id, spec, caller)
    return Installed(template, "published", f"{semver} {object_id}, disabled; test {cost}")


def next_patch(taken: list[str]) -> str:
    if not taken:
        return "0.1.0"
    major, minor, patch = max(tuple(int(p) for p in s.split(".")) for s in taken)
    return f"{major}.{minor}.{patch + 1}"


def add_disabled_trigger(
    svc: EngineService, item: str, object_id: str, spec: rows.Spec, caller: Caller
) -> None:
    """Written disabled in one insert, so no tick can ever see it enabled."""
    now = svc.ctx.clock.now()
    trigger = rows.Trigger(
        id=f"trigger-{secrets.token_hex(6)}",
        workflow_item=item,
        pinned_object=object_id,
        spec=spec,
        created_by=caller.principal,
        created_at=stamp(now),
        enabled=False,
        next_fire_at=rows.first_fire(spec, now),
    )
    svc.ctx.engine.ledger.write(rows.insert(trigger))


def test_cost(svc: EngineService, run_id: str, seconds: float) -> str:
    with Reader.open(svc.ctx.home) as reader:
        spans = [s for s in reader.spans(run_id) if s.profile is not None]
    tokens: dict[str, int] = {}
    for span in spans:
        for name, count in span.tokens.items():
            tokens[name] = tokens.get(name, 0) + count
    return f"{len(spans)} model spans, tokens {tokens}, {seconds:.0f} s"


@dataclass(frozen=True, slots=True)
class Row:
    template: Template
    status: str
    version: str | None


def listing(svc: EngineService, templates: Iterable[Template] = CATALOG) -> list[Row]:
    return [row(svc, template) for template in templates]


def row(svc: EngineService, template: Template) -> Row:
    versions = svc.versions.list(template.folder)
    if versions:
        latest = versions[-1]
        status = {"enabled": "published, enabled", "archived": "archived"}.get(
            latest.state, "published, disabled"
        )
        return Row(template, status, latest.semver)
    if current_draft(svc, template.folder) is None:
        return Row(template, "not installed", None)
    state = svc.drafts.state(template.folder)
    if template.needs:
        return Row(template, f"{state} draft, needs: {', '.join(template.needs)}", None)
    return Row(template, f"{state} draft", None)
