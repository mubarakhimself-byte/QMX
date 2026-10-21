"""The sub-agent definitions every chat is launched with (engine AD-38, HARNESS-REQUESTS H38).

The `Agent` tool's own `model` argument takes Claude aliases only, and an agent definition reaches
a chat only at launch, so a chat that should run a sub-agent on Kimi or DeepSeek is launched with
one definition naming that model. This module generates that set from the model registry.

**One per role, plus one per model he pins.** A definition's description sits in the main model's
cached prompt, so a set that grew one entry per enabled model would change the cached prefix every
time he enabled a model (42 N21). The default is therefore one definition per role, each resolving
through its role list to the first row the chat can reach, and a per-model definition only for a
model he pins for a role. A pin is named after its provider (`kimi-reviewer` for `kimi/k3`); when
one role takes two rows of one provider, each is named after its model instead, so pinning
`openrouter/deepseek/deepseek-v4.1-flash` and `openrouter/qwen/qwen3.6-plus` to `reviewer` gives
`deepseek-reviewer` and `qwen-reviewer`.

**Filtered by the chat's lanes.** The set is regenerated at every launch, so a definition the chat
cannot reach now is left out and one it can join at the next relaunch by resuming the session
(42 N7):

| The chat's main | plan rows | GPT rows | key rows |
| --- | --- | --- | --- |
| plan | all | only with the plan lane on and the row `proven` (P4) | the same |
| GPT | none | all | only when probe P1k passed for a GPT main |
| key | none | none | all |

A plan or GPT row under a key main, and a plan row under a GPT main, is refused by the router,
which is why none is offered: a Claude id on a chat with no plan grant goes through `delegate` v2.
A provider whose `use` is `test_only` (OpenRouter) reaches only a chat whose own main is that
provider, which is a provider-proof lane.

`ROLE_TIERS` is the same table as `qmx_engine.settings.ROLE_TIERS`: the engine generates its role
lists from the registry by the same rule, and one module should own both once the engine reads its
lists from here. The description and prompt of each role are this module's own.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal

from qmx_router.profiles import ProfileName
from qmx_router.registry import ModelRow, QmxId, Registry, UnknownModel

type Lane = Literal["plan", "gpt", "key"]

ROLE_TIERS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "triage": "cheap",
        "clarifier": "cheap",
        "scanner": "cheap",
        "doctor": "cheap",
        "judge": "cheap",
        "reader": "mid",
        "searcher": "mid",
        "writer": "mid",
        "extractor": "mid",
        "planner": "strong",
        "synthesiser": "strong",
        "builder": "strong",
        "reviewer": "strong",
    }
)
CHINESE: Final = frozenset({"kimi", "moonshot", "deepseek", "glm", "zai", "qwen", "minimax"})
"""The profiles whose rows lead every tier (ruling 107)."""

GPT_MAIN_KEY_LANE: Final = True
"""Whether a GPT main may name a third-party sub-agent: probe P1k's GPT row passed on 2026-10-20
(`owner-rtr6-p1k-gpt.log`). False leaves a GPT main its own rows, and `delegate` v2 for the rest."""

ROLE_TEXT: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "triage": (
            "Sorts a pile of items by what deserves attention first. Cheap and quick.",
            "Rank the items you are given. Answer as one ordered list with a one-line reason "
            "each, and nothing else.",
        ),
        "clarifier": (
            "Turns a vague ask into the few questions whose answers change the work.",
            "Read the ask you are given and return at most five questions whose answers would "
            "change what is done. Say why each matters in one line.",
        ),
        "scanner": (
            "Skims a source and reports whether it holds anything worth a closer read.",
            "Skim the source you are given. Answer with the three most important facts it holds, "
            "or that it holds nothing new, each with where in the source it came from.",
        ),
        "doctor": (
            "Diagnoses a failure from its logs and names the cause.",
            "Read the failure and its evidence. Name the most likely cause, the evidence for it, "
            "and the one check that would confirm it. Propose no fix you cannot support.",
        ),
        "judge": (
            "Grades one answer against the criteria it was asked to meet.",
            "Grade the answer you are given against the criteria. Answer pass or fail on the "
            "first line, then each criterion with what met it or did not. Never soften a fail.",
        ),
        "reader": (
            "Reads one long document and reports what it says.",
            "Read the document you are given. Report its claims with where each was found, and "
            "list what it leaves unresolved. Quote figures exactly.",
        ),
        "searcher": (
            "Finds sources and reports what each one is worth.",
            "Find sources for the question you are given. For each, give its location, what it "
            "claims, and how much weight it carries. Say plainly when the evidence is thin.",
        ),
        "writer": (
            "Drafts prose to a brief and a length.",
            "Write the piece you are asked for, to its brief and its length. Plain sentences, no "
            "preamble, no headings unless asked.",
        ),
        "extractor": (
            "Pulls structured records out of unstructured text.",
            "Extract the records you are asked for from the text. Answer as JSON and nothing "
            "else, one object per record, with no field you were given no value for.",
        ),
        "planner": (
            "Breaks an outcome into steps that can each be checked.",
            "Break the outcome you are given into ordered steps. For each, say what it produces "
            "and how someone can tell it worked. Flag a step that rests on an unproven guess.",
        ),
        "synthesiser": (
            "Merges several accounts into one that keeps their disagreements visible.",
            "Merge the accounts you are given. Keep what they agree on, name each disagreement "
            "and which one matters most, and never average away a contradiction.",
        ),
        "builder": (
            "Writes and changes code for one scoped task, and says what it verified.",
            "Make the change you are asked for. Report the files you changed, the command you ran "
            "to check it, and what is still untested. Change nothing outside the task.",
        ),
        "reviewer": (
            "Reviews a change or a claim and reports what is wrong with it.",
            "Review what you are given against its purpose. List each real defect with where it "
            "is and why it matters, then the risks you cannot settle. Say nothing about style "
            "unless it hides a defect.",
        ),
    }
)
"""Each role's one-line description, which the main model reads, and its prompt."""


@dataclass(frozen=True)
class Main:
    """The chat's own model: the profile it launched on and the model it names."""

    profile: ProfileName
    model: str = ""


@dataclass(frozen=True)
class Definition:
    """One native sub-agent definition, in the shape the SDK's `agents` option takes.

    `model` is the id the CLI sends unchanged: a plan row's own alias, which no router is in the
    path of, or a third-party row's `qmx_id`, which the router resolves to that provider."""

    name: str
    description: str
    prompt: str
    model: str
    role: str
    pinned: bool = False


def generated(registry: Registry) -> Mapping[str, tuple[str, ...]]:
    """Each role's candidate rows, from the registry by class: key rows first with the Chinese
    rows leading every tier, then GPT, then the plan (ruling 107). A provider-proof row is never
    generated; only a pin may name one."""
    found: dict[str, tuple[str, ...]] = {}
    for role, tier in ROLE_TIERS.items():
        chosen = sorted(
            (row for row in registry.rows() if row.class_ == tier and _ordinary(registry, row)),
            key=_lane,
        )
        found[role] = tuple(dict.fromkeys(row.qmx_id for row in chosen))
    return found


def definitions(
    registry: Registry,
    main: Main,
    *,
    plan_lane: bool = False,
    roles: Mapping[str, Sequence[str]] | None = None,
    pins: Mapping[str, Sequence[str]] | None = None,
    gpt_key_lane: bool = GPT_MAIN_KEY_LANE,
) -> dict[str, Definition]:
    """This launch's definitions by name, sorted. `roles` are the Settings role lists, generated
    from the registry when a host passes none; `pins` are his per-model additions, by role.
    `plan_lane` is the Claude account's own switch, off until P4 and P2 pass (RTR7, not built
    while P0 fails)."""
    try:
        lane = _Lanes(
            kind=registry.provider(main.profile).kind,
            plan_lane=plan_lane,
            gpt_key_lane=gpt_key_lane,
        )
    except UnknownModel:
        return {}
    rows: dict[str, ModelRow] = {str(row.qmx_id): row for row in registry.rows()}
    found: dict[str, Definition] = {}
    for role, wanted in (roles if roles is not None else generated(registry)).items():
        text = ROLE_TEXT.get(role)
        row = _first(registry, rows, wanted, main.profile, lane)
        if text is not None and row is not None:
            found[role] = _definition(role, text, row)
    for role, wanted in (pins or {}).items():
        text = ROLE_TEXT.get(role)
        if text is None:
            continue
        pinned = [
            row
            for row in (rows.get(qmx_id) for qmx_id in wanted)
            if row is not None and lane.admits(registry, row, main.profile)
        ]
        for name, row in zip(_pin_names(role, pinned), pinned, strict=True):
            found[name] = _definition(role, text, row, name=name)
    return dict(sorted(found.items()))


@dataclass(frozen=True)
class _Lanes:
    """Which of the router's lanes one chat's main reaches, from the table in the module
    docstring."""

    kind: Lane
    plan_lane: bool
    gpt_key_lane: bool

    def admits(self, registry: Registry, row: ModelRow, main: ProfileName) -> bool:
        provider = registry.providers.get(row.provider)
        if provider is None or (provider.use == "test_only" and provider.name != main):
            return False
        match provider.kind:
            case "plan":
                return self.kind == "plan"
            case "gpt":
                return self.kind == "gpt" or self._plan(row)
            case _:
                return (
                    self.kind == "key"
                    or self._plan(row)
                    or (self.kind == "gpt" and self.gpt_key_lane)
                )

    def _plan(self, row: ModelRow) -> bool:
        """A third-party row runs as a native sub-agent under a plan main only while the account's
        plan lane is on and probe P4 found that provider `proven` (AD-38)."""
        return self.kind == "plan" and self.plan_lane and row.plan_main_native == "proven"


def _ordinary(registry: Registry, row: ModelRow) -> bool:
    """A row a role list may name: its provider loads and is not provider-proof only."""
    provider = registry.providers.get(row.provider)
    return provider is not None and provider.use != "test_only"


def _first(
    registry: Registry,
    rows: Mapping[str, ModelRow],
    wanted: Sequence[str],
    main: ProfileName,
    lane: _Lanes,
) -> ModelRow | None:
    for qmx_id in wanted:
        row = rows.get(qmx_id)
        if row is not None and lane.admits(registry, row, main):
            return row
    return None


def _definition(
    role: str, text: tuple[str, str], row: ModelRow, *, name: str | None = None
) -> Definition:
    """A role's definition, or a pinned one when `name` is given. A plan row is addressed by the
    CLI's own alias and a third-party row by its `qmx_id`, which is what the router resolves."""
    pinned = name is not None
    return Definition(
        name=name or role,
        description=f"{text[0]} Runs on {row.qmx_id}." if pinned else text[0],
        prompt=text[1],
        model=str(row.native if row.provider == ProfileName("claude") else row.qmx_id),
        role=role,
        pinned=pinned,
    )


def _pin_names(role: str, rows: Sequence[ModelRow]) -> list[str]:
    """`<provider>-<role>` for each pinned row, and `<model>-<role>` instead when one role takes
    two rows of one provider, so `openrouter`'s DeepSeek and Qwen rows are `deepseek-reviewer` and
    `qwen-reviewer` rather than one name for two models."""
    counts: dict[ProfileName, int] = {}
    for row in rows:
        counts[row.provider] = counts.get(row.provider, 0) + 1
    names = [
        f"{_tail_head(row) if counts[row.provider] > 1 else row.provider}-{role}" for row in rows
    ]
    if len(set(names)) != len(names):
        names = [f"{_tail_head(row)}-{index}-{role}" for index, row in enumerate(rows, start=1)]
    return names


def _tail_head(row: ModelRow) -> str:
    """The first segment of a row's id after its provider: `openrouter/deepseek/deepseek-v4.1-flash`
    is `deepseek`, so two rows of one provider still read as the models they are."""
    return QmxId(row.qmx_id).removeprefix(f"{row.provider}/").split("/")[0]


def _lane(row: ModelRow) -> tuple[int, int]:
    """Key rows before GPT before the plan, Chinese rows first inside a lane."""
    return {"claude": 2, "gpt": 1}.get(row.provider, 0), 0 if row.provider in CHINESE else 1
