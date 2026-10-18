"""`versions.publish`, `versions.list`, enable, disable and archive (SOLUTION-DESIGN 6.1, 13): the
version half of the AD-11 lifecycle.

Publishing merges a tested draft into `main` with its semver; the Library copies `tested-by` when
the content hash is unchanged, and a second publish of one hash creates nothing. Enabling needs a
passing run for the version's content hash, whatever the merge did. A version's state after
publish is its latest `state` annotation; nothing is removed, so an archived version keeps its runs
and lineage.
"""

from __future__ import annotations

from dataclasses import dataclass

from qmx_engine.definition.validate import needs_line, validate
from qmx_engine.ports.library import MAIN, Stored, drafts_ref
from qmx_engine.service.context import Act, Caller, Context, Refused, State, require
from qmx_engine.service.drafts import Drafts
from qmx_engine.service.runs import Runs


def operator_only(caller: Caller, act: Act) -> None:
    """Publish and enable take the operator's yes (AD-22). A copilot reaches them only through a
    MANAGE door, which asks him first and then calls as him."""
    if caller.kind != "user":
        raise Refused("operator_only", f"only the operator may {act}; a {caller.kind} may not")


@dataclass(frozen=True, slots=True)
class Version:
    object_id: str
    item: str
    semver: str
    content_hash: str
    state: State
    tested: bool


class Versions:
    def __init__(self, ctx: Context, drafts: Drafts, runs: Runs) -> None:
        self.ctx = ctx
        self.drafts = drafts
        self.runs = runs

    def publish(self, item: str, semver: str, *, caller: Caller) -> str:
        operator_only(caller, "publish")
        library = self.ctx.library
        require(self.drafts.state(item), "publish", f"draft {item}")
        draft = self.drafts.get(item)
        problems = validate(draft.bundle.folder(), roles=self.ctx.roles(), publish=True)
        if problems:
            codes = " ".join(sorted({p.code for p in problems}))
            raise Refused("invalid", f"draft {item} cannot publish: {codes}")
        object_id = library.publish(item, drafts_ref(item), semver, principal=caller.principal)
        parent = library.get(draft.object_id).fields.get("variant_of")
        if isinstance(parent, dict):
            to = str(parent.get("object_id"))
            library.link(object_id, "variant-of", to, principal=caller.principal)
        return object_id

    def get(self, object_id: str) -> Version:
        stored = self.ctx.library.get(object_id)
        if stored.kind != "workflow" or stored.ref != MAIN:
            raise Refused("not_a_version", f"{object_id} is not a published version")
        return self.view(stored)

    def view(self, stored: Stored) -> Version:
        content_hash = str(stored.fields.get("content_hash"))
        return Version(
            stored.object_id,
            stored.item,
            str(stored.fields.get("semver")),
            content_hash,
            self.runs.version_state(stored),
            self.drafts.tested(stored.item, content_hash),
        )

    def list(self, item: str) -> list[Version]:
        return [self.view(s) for s in self.ctx.library.objects(item, "workflow", MAIN)]

    def enable(self, object_id: str, *, caller: Caller) -> Version:
        operator_only(caller, "enable")
        version = self.get(object_id)
        require(version.state, "enable", f"version {version.semver} of {version.item}")
        needs = self.ctx.library.get_object(object_id).needs()
        if needs:
            raise Refused("needs_unmet", f"{version.item} cannot be enabled; {needs_line(needs)}")
        if not version.tested:
            raise Refused(
                "not_tested",
                f"no passing run for content hash {version.content_hash}; test it first",
            )
        return self.move(version, "enable", "enabled", caller)

    def disable(self, object_id: str, *, caller: Caller) -> Version:
        return self.move(self.get(object_id), "disable", "disabled", caller)

    def archive(self, object_id: str, *, caller: Caller) -> Version:
        return self.move(self.get(object_id), "archive", "archived", caller)

    def move(self, version: Version, act: Act, to: State, caller: Caller) -> Version:
        require(version.state, act, f"version {version.semver} of {version.item}")
        self.ctx.library.annotate(version.object_id, "state", to, principal=caller.principal)
        return self.get(version.object_id)
