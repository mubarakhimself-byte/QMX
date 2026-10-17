"""`tests.run` (SOLUTION-DESIGN 6.2, 13): a draft run in test mode, its `test-report` bound to the
draft's content hash, on the run's own branch.

A variant is first saved as its resolved snapshot, a new draft revision that remembers its parent,
so what is tested is what will publish. A full test that passes links the draft `tested-by` the
run; a selected-subgraph test writes its report but tests only that part, so it marks nothing, and
so does a run on the fake provider, which proves nothing about a real model (ruling 51).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from pydantic import JsonValue

from qmx_engine.definition.validate import needs_line
from qmx_engine.ports.library import JsonObject, RunStatus
from qmx_engine.service.context import Caller, Context, Refused
from qmx_engine.service.drafts import Drafts
from qmx_engine.service.runs import run_bundle


@dataclass(frozen=True, slots=True)
class TestReport:
    report_id: str
    run_id: str
    workflow_item: str
    content_hash: str
    status: RunStatus
    reason: str | None
    subgraph: list[str] | None
    stale: bool
    """True once the draft's content hash moved past the one this report is bound to."""


class Tests:
    def __init__(self, ctx: Context, drafts: Drafts) -> None:
        self.ctx = ctx
        self.drafts = drafts

    async def run(
        self,
        item: str,
        *,
        caller: Caller,
        inputs: JsonValue = None,
        subgraph: list[str] | None = None,
        fake: bool = False,
        run_id: str | None = None,
    ) -> TestReport:
        """`fake` answers model nodes with the fake provider, for a run that spends nothing."""
        library = self.ctx.library
        draft = self.drafts.get(item)
        problems = self.drafts.problems(draft.bundle)
        if problems:
            codes = " ".join(sorted({p.code for p in problems}))
            raise Refused("invalid", f"draft {item} does not validate: {codes}")
        bundle, variant_of = self.drafts.resolved(draft.bundle)
        if bundle.needs():
            raise Refused(
                "needs_unmet", f"draft {item} cannot be tested; {needs_line(bundle.needs())}"
            )
        if variant_of is not None:
            fields: JsonObject = {"caller_kind": caller.kind, "variant_of": variant_of}
            draft = library.put_draft(
                item, bundle, draft.revision, principal=caller.principal, fields=fields
            )
        content_hash = str(bundle.content_hash())
        outcome, summary = await run_bundle(
            self.ctx,
            bundle,
            object_id=draft.object_id,
            item=item,
            mode="test",
            inputs=inputs,
            subgraph=subgraph,
            caller=caller,
            fake=fake,
            run_id=run_id,
        )
        principal = f"run:{outcome.run_id}"
        report: JsonObject = {
            "workflow_item": item,
            "run_id": outcome.run_id,
            "draft_object_id": draft.object_id,
            "status": outcome.status,
            "reason": summary.fields.get("reason"),
            "subgraph": list[JsonValue](subgraph) if subgraph is not None else None,
            "caller_kind": caller.kind,
            "fake": fake,
        }
        stored = library.put_test_report(content_hash, report, principal=principal)
        if outcome.status == "passed" and subgraph is None and not fake:
            library.link(draft.object_id, "tested-by", summary.object_id, principal=principal)
        return self.read(stored.object_id, content_hash)

    def report(self, item: str) -> TestReport | None:
        """The latest full test report of the draft, stale or not."""
        reports = [
            r
            for r in self.ctx.library.objects(item, "test-report")
            if r.fields.get("subgraph") is None
        ]
        if not reports:
            return None
        bundle, _ = self.drafts.resolved(self.drafts.get(item).bundle)
        return self.read(reports[-1].object_id, bundle.content_hash())

    def read(self, report_id: str, current_hash: str | None) -> TestReport:
        fields = self.ctx.library.get(report_id).fields
        subgraph = fields.get("subgraph")
        reason = fields.get("reason")
        return TestReport(
            report_id=report_id,
            run_id=str(fields.get("run_id")),
            workflow_item=str(fields.get("workflow_item")),
            content_hash=str(fields.get("content_hash")),
            status=cast(RunStatus, fields.get("status")),
            reason=reason if isinstance(reason, str) else None,
            subgraph=[str(n) for n in subgraph] if isinstance(subgraph, list) else None,
            stale=fields.get("content_hash") != current_hash,
        )
