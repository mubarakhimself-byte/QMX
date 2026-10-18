"""`drafts.get`, `drafts.put` and `drafts.validate` (SOLUTION-DESIGN 13), and the draft half of the
AD-11 lifecycle.

A draft is the head of `refs/drafts/<item>`. It is `validated` when it validates against the
Settings `[roles]`, and `tested` when some revision with the same content hash has a `tested-by`
edge to a `workflow-run` that `passed`, in either mode. Testing keys on the hash, so moving a node
keeps the mark and any real edit loses it. A variant (`extends`) is resolved over its parent
before it validates, tests or publishes (AD-11).
"""

from __future__ import annotations

from typing import cast

from qmx_engine.definition.folder import Problem
from qmx_engine.definition.overlay import OverlayError, resolve
from qmx_engine.definition.validate import validate
from qmx_engine.ports.library import Bundle, Draft, JsonObject, LibraryRefused, drafts_ref
from qmx_engine.service.context import Caller, Context, State


class Drafts:
    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx

    def get(self, item: str) -> Draft:
        return self.ctx.library.get_draft(item, drafts_ref(item))

    def put(
        self, item: str | None, bundle: Bundle, expected_revision: int, *, caller: Caller
    ) -> Draft:
        """Save a draft. An edit gives it a new revision; a test report for the old content hash
        then reads stale."""
        return self.ctx.library.put_draft(
            item,
            bundle,
            expected_revision,
            principal=caller.principal,
            fields={"caller_kind": caller.kind},
        )

    def resolved(self, bundle: Bundle) -> tuple[Bundle, JsonObject | None]:
        """A variant as its full snapshot over its parent's files, with its parent for the
        publisher's `variant-of` edge; any other draft as it is."""
        if bundle.definition.get("extends") is None:
            return bundle, None
        extends = cast(JsonObject, bundle.definition["extends"])
        parent = self.ctx.library.get_object(str(extends.get("object_id")))
        found = resolve(bundle.definition, parent.definition)
        item, object_id = found.variant_of
        files = {**parent.files, **bundle.files}
        return Bundle(found.snapshot, files), {"workflow_item": item, "object_id": object_id}

    def problems(self, bundle: Bundle) -> list[Problem]:
        try:
            bundle, _ = self.resolved(bundle)
        except (OverlayError, LibraryRefused, ValueError) as error:
            return [Problem("extends_invalid", "extends", str(error))]
        return validate(bundle.folder(), roles=self.ctx.roles())

    def validate(self, item: str) -> list[Problem]:
        return self.problems(self.get(item).bundle)

    def tested(self, item: str, content_hash: str | None) -> bool:
        library = self.ctx.library
        if content_hash is None:
            return False
        for stored in library.objects(item, "workflow"):
            if stored.fields.get("content_hash") != content_hash:
                continue
            for edge in library.edges(stored.object_id, "tested-by"):
                if library.get(edge.to_id).fields.get("status") == "passed":
                    return True
        return False

    def state(self, item: str) -> State:
        draft = self.get(item)
        if self.problems(draft.bundle):
            return "draft"
        bundle, _ = self.resolved(draft.bundle)
        return "tested" if self.tested(item, bundle.content_hash()) else "validated"
