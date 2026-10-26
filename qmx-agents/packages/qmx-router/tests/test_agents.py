"""What each chat's `Agent` tool is offered (AD-38, H38): one definition per role, plus one per
pinned model, filtered by the lanes the chat can reach."""

from __future__ import annotations

from pathlib import Path

from qmx_router.agents import GPT_MAIN_KEY_LANE, ROLE_TIERS, Main, definitions, generated
from qmx_router.profiles import ProfileName
from qmx_router.registry import bundled, load

KIMI = Main(ProfileName("kimi"))
PLAN = Main(ProfileName("claude"), "haiku")
GPT = Main(ProfileName("gpt"), "gpt-6.1-sol")
OPENROUTER = Main(ProfileName("openrouter"), "openrouter/moonshotai/kimi-k2.5")
ROLES = tuple(sorted(ROLE_TIERS))
DEEPSEEK = "deepseek/deepseek-v4-pro"
PROVEN = 'plan_main_native = "proven"\n'


def test_a_key_main_lists_one_definition_per_role() -> None:
    found = definitions(bundled(), KIMI)
    assert tuple(found) == ROLES
    assert found["reviewer"].model == DEEPSEEK
    assert found["triage"].model == "deepseek/deepseek-flash"
    assert found["writer"].model == "glm/glm-5.3"
    assert found["reviewer"].description.startswith("Reviews a change")
    assert found["reviewer"].prompt.startswith("Review what you are given")
    assert not any(definition.pinned for definition in found.values())


def test_a_plan_main_gets_third_party_definitions_only_from_a_proven_row_and_an_on_lane(
    tmp_path: Path,
) -> None:
    (tmp_path / "deepseek.toml").write_text(f"[defaults]\n{PROVEN}", encoding="utf-8")
    proven = load(tmp_path)
    off = definitions(proven, PLAN)
    dark = definitions(proven, PLAN, plan_lane=False)
    on = definitions(proven, PLAN, plan_lane=True)
    unproven = definitions(bundled(), PLAN, plan_lane=True)
    assert {definition.model for definition in off.values()} == {"haiku", "sonnet", "opus"}
    assert off == dark
    assert off == unproven
    assert on["reviewer"].model == DEEPSEEK
    assert on["triage"].model == "deepseek/deepseek-flash"


def test_a_pinned_model_adds_one_definition_named_after_its_provider() -> None:
    plain = definitions(bundled(), KIMI)
    pinned = definitions(bundled(), KIMI, pins={"reviewer": [DEEPSEEK]})
    added = {name: found for name, found in pinned.items() if name not in plain}
    assert tuple(added) == ("deepseek-reviewer",)
    assert added["deepseek-reviewer"].model == DEEPSEEK
    assert added["deepseek-reviewer"].pinned
    assert len(pinned) == len(plain) + 1


def test_two_pins_of_one_provider_for_one_role_are_named_after_their_models() -> None:
    found = definitions(
        bundled(),
        OPENROUTER,
        pins={
            "reviewer": [
                "openrouter/deepseek/deepseek-v4.1-flash",
                "openrouter/qwen/qwen3.6-plus",
            ]
        },
    )
    assert found["deepseek-reviewer"].model == "openrouter/deepseek/deepseek-v4.1-flash"
    assert found["qwen-reviewer"].model == "openrouter/qwen/qwen3.6-plus"
    assert len(found) == len(ROLES) + 2


def test_a_provider_proof_row_reaches_only_its_own_main(tmp_path: Path) -> None:
    (tmp_path / "openrouter.toml").write_text('use = "test_only"\n', encoding="utf-8")
    proof = load(tmp_path)
    pinned = {"reviewer": ["openrouter/deepseek/deepseek-v4.1-flash"]}
    assert "openrouter-reviewer" not in definitions(proof, KIMI, pins=pinned)
    assert "openrouter-reviewer" in definitions(proof, OPENROUTER, pins=pinned)
    roles = [qmx_id for wanted in generated(proof).values() for qmx_id in wanted]
    assert not any(qmx_id.startswith("openrouter/") for qmx_id in roles)


def test_the_bundled_openrouter_rows_join_the_generated_role_lists() -> None:
    roles = generated(bundled())
    assert "openrouter/moonshotai/kimi-k2.5" in roles["reviewer"]
    assert "openrouter/deepseek/deepseek-v4.1-flash" in roles["triage"]
    assert "openrouter-reviewer" in definitions(
        bundled(), KIMI, pins={"reviewer": ["openrouter/deepseek/deepseek-v4.1-flash"]}
    )


def test_a_gpt_main_lists_key_rows_only_when_p1k_passed() -> None:
    passed = definitions(bundled(), GPT, gpt_key_lane=True)
    failed = definitions(bundled(), GPT, gpt_key_lane=False)
    assert passed["reviewer"].model == DEEPSEEK
    assert failed["reviewer"].model == "gpt/gpt-6.1-sol"
    assert tuple(failed) == ("builder", "planner", "reviewer", "synthesiser")
    assert all(definition.model.startswith("gpt/") for definition in failed.values())
    assert GPT_MAIN_KEY_LANE is True


def test_a_chat_on_a_profile_the_registry_does_not_hold_gets_none() -> None:
    assert definitions(bundled(), Main(ProfileName("nowhere"))) == {}
