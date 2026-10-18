"""Story 40.5 — Quant ontology and opaque actor identities (FR-Q06)."""

from __future__ import annotations

import pytest
from qma.core import ontology as ontology_api
from qma.core.ontology import (
    DESK_DISPLAY_NAMES,
    DESK_PREFIX_TOKENS,
    DESK_SLUG_VALUES,
    ONTOLOGY_CHAIN,
    ONTOLOGY_OBJECTS,
    PROFILE_FORBIDDEN_USES,
    ROLE_DISPLAY_NAMES,
    RUN_CONTAINER,
    WORK_VOCABULARY,
    ActorId,
    DeskSlug,
    OntologyError,
    Profile,
    Worker,
    assert_profile_presentation_only,
    assert_role_names_are_not_desk_names,
    is_ontology_object,
)
from qma.core.plugins.manifest import DESK_PREFIX_TOKENS as MANIFEST_DESK_PREFIXES
from qma.core.refusals import SlugUnavailable
from qmf.core.refusal import is_ok, is_refusal


def test_ontology_chain_and_work_vocabulary() -> None:
    assert ONTOLOGY_CHAIN == ("Desk", "Role", "Quant", "Agent", "Subagent")
    assert frozenset(ONTOLOGY_CHAIN) == ONTOLOGY_OBJECTS
    assert RUN_CONTAINER == "Session"
    assert WORK_VOCABULARY == ("Goal", "Mission", "Task")
    assert is_ontology_object("Quant") is True
    assert is_ontology_object("Session") is False
    assert is_ontology_object("Worker") is False
    assert isinstance(Worker(address="worker://slot-1"), Worker)


def test_desk_slugs_exactly_five_and_shared_with_plugin_prefixes() -> None:
    assert (
        frozenset({"research", "trading", "dev", "analysis", "pm"}) == DESK_SLUG_VALUES
    )
    assert DESK_PREFIX_TOKENS == DESK_SLUG_VALUES
    assert MANIFEST_DESK_PREFIXES == DESK_PREFIX_TOKENS
    assert set(DeskSlug) == {
        DeskSlug.RESEARCH,
        DeskSlug.TRADING,
        DeskSlug.DEV,
        DeskSlug.ANALYSIS,
        DeskSlug.PM,
    }
    assert (
        frozenset({"Researcher", "Trader", "Developer", "Analyst", "Product Manager"})
        == ROLE_DISPLAY_NAMES
    )
    assert set(DESK_DISPLAY_NAMES.values()) == {
        "Research",
        "Trading",
        "Development",
        "Analysis",
        "PM",
    }


def test_static_checks_reject_role_name_as_desk_name() -> None:
    assert_role_names_are_not_desk_names()
    assert frozenset(DESK_DISPLAY_NAMES.values()).isdisjoint(ROLE_DISPLAY_NAMES)


def test_actor_id_opaque_grammar_and_serialization() -> None:
    minted = ActorId.mint(DeskSlug.RESEARCH, "alpha")
    assert is_ok(minted)
    actor = minted.value
    assert actor.serialize() == "quant:research/alpha"
    assert str(actor) == "quant:research/alpha"
    assert not hasattr(actor, "desk_slug")
    assert not hasattr(actor, "quant_slug")

    roundtrip = ActorId.try_create(actor.serialize())
    assert is_ok(roundtrip)
    assert roundtrip.value == actor

    bad = ActorId.try_create("quant:ops/alpha")
    assert is_refusal(bad)
    assert SlugUnavailable.matches(bad)

    bad_form = ActorId.mint("RESEARCH", "alpha")
    assert is_refusal(bad_form)


def test_profile_is_presentation_only() -> None:
    profile = Profile(display_name="Labs", desk_slugs=(DeskSlug.RESEARCH, DeskSlug.DEV))
    assert profile.display_name == "Labs"
    assert (
        frozenset(
            {
                "daemon_state",
                "identity_segment",
                "index",
                "filter",
                "permission_key",
                "routing_key",
            }
        )
        == PROFILE_FORBIDDEN_USES
    )
    for use in PROFILE_FORBIDDEN_USES:
        with pytest.raises(OntologyError, match="presentation-only"):
            assert_profile_presentation_only(use)
    assert_profile_presentation_only("client_display")


def test_package_export_surface() -> None:
    assert ontology_api.ActorId is ActorId
    assert ontology_api.ONTOLOGY_CHAIN == ONTOLOGY_CHAIN
    assert "Worker" in ontology_api.__all__
