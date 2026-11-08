"""Story 30.6: a regime model registration enters the node's passive hub as sandbox.

Moved here from the regime register when the node's reading blocks became
``qmf.readings`` (C-08): the passive hub is the node's, so the crossing into it
lives in the node and the readings package never imports ``qmn``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from qmf.core import Fingerprint, Ok, Result, WriterId, fingerprint_bytes, is_refusal
from qmf.readings.regime_register import REGIME_REGISTER_ARTIFACT_ID, RegistrationLineageBundle

from qmn.promotion._refuse import clean_token, invalid, policy
from qmn.promotion.hub import SANDBOX_PROVENANCE, HubArtifact, refuse_sandbox_provenance
from qmn.promotion.passive_hub import HubFragment, PassiveHubTree, accept_inbox_fragment

__all__ = ["SandboxHubPublication", "enter_passive_hub_as_sandbox"]


@dataclass(frozen=True, slots=True)
class SandboxHubPublication:
    """Passive-hub inbox accept that keeps sandbox provenance visible."""

    registration_fp: Fingerprint
    hub_artifact: HubArtifact
    provenance: str
    write_only_inbox: bool
    promotion_refused: bool
    publish_refused: bool
    composition_fp_unchanged: bool

    def as_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "registration_fp": self.registration_fp.value,
                "artifact_key": self.hub_artifact.artifact_key,
                "fp1": self.hub_artifact.fp1.value,
                "provenance": self.provenance,
                "write_only_inbox": self.write_only_inbox,
                "promotion_refused": self.promotion_refused,
                "publish_refused": self.publish_refused,
                "composition_fp_unchanged": self.composition_fp_unchanged,
            }
        )


def enter_passive_hub_as_sandbox(
    bundle: object,
    *,
    tree: object,
    writer: object,
    artifact_key: object | None = None,
) -> Result[SandboxHubPublication]:
    """Accept the registration into the passive-hub inbox with sandbox provenance.

    Promotion publish/pull still refuse sandbox provenance until the separate
    human/recertification path (Story 30.8). Inbox write never changes
    ``composition_fp``.
    """
    if not isinstance(bundle, RegistrationLineageBundle):
        return invalid(
            "bundle",
            "passive-hub entry takes a RegistrationLineageBundle",
            given=type(bundle).__name__,
        )
    if not isinstance(tree, PassiveHubTree):
        return invalid(
            "tree",
            "passive-hub entry takes a PassiveHubTree",
            given=type(tree).__name__,
        )
    if not isinstance(writer, WriterId):
        return invalid("writer", "hub fragments are WriterId-scoped", given=type(writer).__name__)

    key_token = clean_token(artifact_key) or REGIME_REGISTER_ARTIFACT_ID
    payload = json.dumps(
        bundle.registration.as_jsonable(),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    payload_fp = fingerprint_bytes(payload)
    hub_artifact = HubArtifact.try_create(
        artifact_key=key_token,
        fp1=payload_fp,
        provenance=SANDBOX_PROVENANCE,
    )
    if is_refusal(hub_artifact):
        return hub_artifact
    fragment = HubFragment.try_create(
        artifact_key=hub_artifact.value.artifact_key,
        fp1=hub_artifact.value.fp1,
        provenance=hub_artifact.value.provenance,
        writer=writer,
        payload=payload,
    )
    if is_refusal(fragment):
        return fragment
    accepted = accept_inbox_fragment(tree, fragment.value)
    if is_refusal(accepted):
        return accepted

    # Promotion rules still refuse sandbox provenance at publish and pull.
    publish_gate = refuse_sandbox_provenance(SANDBOX_PROVENANCE, crossing="publish")
    pull_gate = refuse_sandbox_provenance(SANDBOX_PROVENANCE, crossing="pull")
    if not is_refusal(publish_gate) or not is_refusal(pull_gate):
        return policy(
            "provenance",
            "sandbox provenance must remain refused at publish and pull after hub entry",
            failure_id="mis.regime_register.sandbox_gate_leak",
        )

    return Ok(
        SandboxHubPublication(
            registration_fp=bundle.registration_fp,
            hub_artifact=hub_artifact.value,
            provenance=SANDBOX_PROVENANCE,
            write_only_inbox=True,
            promotion_refused=True,
            publish_refused=True,
            composition_fp_unchanged=True,
        )
    )
