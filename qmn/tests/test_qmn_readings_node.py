"""The node's own seams around the reading blocks: its workload law and its passive hub.

These two tests moved from the readings suite when the blocks left the node (C-08), because
each crosses into ``qmn``: the light/heavy workload law and the passive-hub inbox.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from qmf.core import Instant, RefusalCategory, WriterId, fingerprint, is_ok, is_refusal
from qmf.core.refusal import Result
from qmf.readings import IDENTITY_PRODUCER_ID, configure_mis_producer
from qmf.readings.regime_register import (
    SANDBOX_PROVENANCE as READINGS_SANDBOX_PROVENANCE,
)
from qmf.readings.regime_register import (
    CandidateKind,
    assert_registration_preserves_composition_fp,
    build_non_authoritative_registration,
    install_regime_model_kind,
    register_model_lineage,
)
from qmf.registry import EdgeLog, KindRegistry, Registrar
from qmn.host.light_heavy import (
    CompositionClass,
    FourBoundDeclaration,
    WorkloadClaim,
    WorkloadKind,
    evaluate_workload_claim,
)
from qmn.promotion.hub import SANDBOX_PROVENANCE
from qmn.promotion.passive_hub import PassiveHubTree, publish_inbox_fragment
from qmn.promotion.readings_hub import enter_passive_hub_as_sandbox

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def test_ad24_heavy_by_default_light_claim_refused_without_baseline() -> None:
    configured = _ok(configure_mis_producer(IDENTITY_PRODUCER_ID))
    assert configured.declared_budget is None
    claim = _ok(
        WorkloadClaim.try_create(
            kind=WorkloadKind.LABELER,
            definition_fp=_ok(configured.fingerprint()),
            live_path_baseline_present=False,
        )
    )
    assignment = _ok(evaluate_workload_claim(claim))
    assert assignment.effective_class is CompositionClass.HEAVY

    bounds = _ok(
        FourBoundDeclaration.try_create(
            per_update_cost_rung="live-path",
            bounded_state=True,
            window_or_anchor_rule="frontier-as-of",
            synchronous_availability=True,
        )
    )
    light_claim = _ok(
        WorkloadClaim.try_create(
            kind=WorkloadKind.PRODUCER,
            definition_fp=_ok(configured.fingerprint()),
            declared_bounds=bounds,
            live_path_baseline_present=False,
            benchmark_proven=True,
        )
    )
    refused = evaluate_workload_claim(light_claim)
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION


def test_the_readings_registration_names_the_hubs_own_sandbox_token() -> None:
    assert READINGS_SANDBOX_PROVENANCE == SANDBOX_PROVENANCE == "sandbox"


def test_passive_hub_keeps_sandbox_and_preserves_composition_fp(tmp_path: Path) -> None:
    registration = _ok(
        build_non_authoritative_registration(
            candidate_kind=CandidateKind.EXTERNAL,
            external_family="hmm",
        )
    )
    composition = _ok(fingerprint({"class": "composition_fp", "label": "hub-epoch"}))
    kinds = KindRegistry()
    _ok(install_regime_model_kind(kinds))
    writer = _ok(WriterId.try_create("op-machine", "mis-register", "regime-model", "boot-30-6"))
    bundle = _ok(
        register_model_lineage(
            registration,
            registrar=Registrar(kinds),
            edge_log=EdgeLog(writer),
            writer=writer,
            sequence=0,
            created_at=_ok(Instant.try_create(1_700_000_100_000_000_000)),
            composition_fp=composition,
        )
    )
    tree = PassiveHubTree(tmp_path / "hub")
    published = _ok(
        enter_passive_hub_as_sandbox(
            bundle,
            tree=tree,
            writer=writer,
            artifact_key="regime-candidate",
        )
    )
    assert published.provenance == SANDBOX_PROVENANCE
    assert published.write_only_inbox is True
    assert published.promotion_refused is True
    assert published.publish_refused is True
    assert published.composition_fp_unchanged is True
    # Operator publish still refuses sandbox provenance.
    refused_publish = publish_inbox_fragment(tree, writer=writer, artifact_key="regime-candidate")
    assert is_refusal(refused_publish)
    assert refused_publish.context["field"] == "provenance"
    assert is_ok(assert_registration_preserves_composition_fp(bundle, composition_fp=composition))
