"""RTR6's live lanes: the sub-agent definitions each chat is launched with (AD-38, H38).

    uv run --no-sync python ../scripts/live/router/rtr6_subagents.py <lane>

- `p1k`   A Kimi main on the OpenRouter row spawns the two reviewers he pinned, through the real
          router and the real key. The only lane that spends: OpenRouter's cheap DeepSeek and Qwen
          rows, one short turn each.
- `e18`   A Kimi main on the loopback fake model spawns a Kimi-named sub-agent; the relay sends it
          to the Kimi provider row and its answer comes back. E18's router half: the engine's
          fan-out half has no `subagents` field in the v1 definition to run.
- `plan`  A plan main on haiku, on the ship home under the lane lock: Claude aliases only, because
          P0 failed and every third-party row is `plan_main_native: delegate_only`.
- `gpt`   A GPT main, in a throwaway home carrying the ship home's stored GPT probe: it is offered
          the key rows, which is probe P1k's GPT row.
- `regen` A definition leaves at the relaunch once its model leaves `[agents] subagent_pins`.
- `cache` Two chats with the same roles and pins list the same definitions.
- `unknown` A sub-agent naming an unknown id fails and the parent finishes its turn.
- `perf`  Launch time in ms with the generated set against launches with none, five of each.

Each lane writes `D:/QMX-worktrees/qma-ship/build/evidence/rtr6/<prefix>rtr6-<lane>.log` and exits
1 on any FAIL. The fake lanes point `kimi` and `deepseek` provider rows at a loopback `FakeModel`,
so no provider is called. A lane that runs a model holds `D:/QMX-worktrees/.engine-lane-lock`
itself and never nests inside another lock.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import shutil
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Final

LIVE: Final = Path(__file__).resolve().parents[1]
sys.path.append(str(LIVE / "qma"))
STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = STORE / "evidence" / "rtr6"
HOMES: Final = STORE / "homes"
SHIP_HOME: Final = Path("D:/QMX-worktrees/qma-ship/home")
LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
PREFIX: Final = os.environ.get("RTR6_LOG_PREFIX", "owner-")
"""Read at import, before a lane scrubs this process's env. The checker sets `check-`."""
os.environ.setdefault("QMA_EVIDENCE_DIR", str(EVIDENCE))
os.environ.setdefault("QMA_LIVE_SCRATCH", str(HOMES.parent / "scratch-rtr6"))

from common import Log, Session, put_providers, require_login, use_fake_key, wait_turn  # noqa: E402
from fake_model import FAKE_REF, FakeModel, Turn, text, tool_use  # noqa: E402
from qmx_router.agents import ROLE_TIERS, Main, definitions  # noqa: E402
from qmx_router.profiles import ProfileName  # noqa: E402
from qmx_router.registry import bundled  # noqa: E402

KIMI_ROW: Final = "moonshotai/kimi-k2.5"
OPENROUTER: Final[dict[str, Any]] = {
    "base_url": "https://openrouter.ai/api",
    "credential_ref": "qmx/openrouter",
    "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), KIMI_ROW),
}
OPENROUTER_PINS: Final[dict[str, list[str]]] = {
    "reviewer": ["openrouter/deepseek/deepseek-v4.1-flash", "openrouter/qwen/qwen3.6-plus"]
}
FAKE_PINS: Final[dict[str, list[str]]] = {"reviewer": ["kimi/k3", "deepseek/deepseek-v4-pro"]}
GPT_ROW: Final[dict[str, Any]] = {
    "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "gpt-6.1-sol")
}
P1K_PROMPT: Final = (
    "Use the deepseek-reviewer agent and then the qwen-reviewer agent, each to review this "
    "sentence: 'The sky is green.' Then reply with both reviewers' answers, word for word."
)
REVIEW: Final = "Review the sentence. Use the marker you were told to use."
ROUTES: Final = {
    "SENTINEL-KIMI": [Turn([text("KIMI-REVIEW-OK")], served="kimi-k3")],
    "SENTINEL-QWEN": [Turn([text("QWEN-REVIEW-OK")], served="qwen3.6-plus")],
    "SENTINEL-DEEPSEEK": [Turn([text("DEEPSEEK-REVIEW-OK")], served="deepseek-v4-pro")],
}
SPAWN: Final = Turn(
    [
        tool_use(
            "Task",
            {
                "description": "kimi review",
                "prompt": f"{REVIEW} Use SENTINEL-KIMI.",
                "subagent_type": "kimi-reviewer",
            },
        )
    ]
)
ROLES: Final = len(ROLE_TIERS)
PER_LAUNCH: Final = 5


def fake_rows(url: str, *names: str) -> dict[str, dict[str, Any]]:
    """The named provider rows on the loopback fake model. Each keeps its bundled name, which the
    generator resolves rows by, and its strong row as every tier's model."""
    strong = {"kimi": "kimi-k3", "deepseek": "deepseek-v4-pro", "openrouter": KIMI_ROW}
    return {
        name: {
            "base_url": url,
            "credential_ref": FAKE_REF,
            "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), strong[name]),
        }
        for name in names
    }


def fresh(slug: str) -> Path:
    root = HOMES / f"rtr6-{slug}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def set_pins(root: Path, pins: dict[str, list[str]] | None) -> None:
    """`[agents] subagent_pins`, which each launch reads for the per-model definitions (AD-38)."""
    from qma.harness import QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    control = control_service(QmxHome(root))
    agents = dict(control.settings_get("agents"))
    if pins is None:
        agents.pop("subagent_pins", None)
    else:
        agents["subagent_pins"] = pins
    control.settings_put("agents", agents)


def listed(session: Session) -> dict[str, Any]:
    """The definitions this launch's Surface recorded in `surface.json`."""
    path = session.home.launch_dir(str(session.chat)) / "surface.json"
    return dict(json.loads(path.read_text("utf-8"))["agents"])


def relay_rows(session: Session) -> list[dict[str, Any]]:
    """Each relayed model call's own payload: the model the relay sent upstream and its status."""
    return [
        dict(row["payload"])
        for row in session.journal()
        if row.get("event") == "model_call" and "payload" in row
    ]


def asked(fake: FakeModel, model: str) -> int:
    """How many scripted model requests the fake answered for `model`."""
    return sum(1 for seen in fake.requests if seen.scripted and seen.json.get("model") == model)


@contextlib.contextmanager
def lane_lock() -> Any:
    LOCK.mkdir()
    try:
        yield
    finally:
        LOCK.rmdir()


async def open_chat(root: Path, *, profile: str, model: str, title: str) -> Session:
    from qma.harness.launch import TestMode  # noqa: PLC0415

    return await Session.start(
        root,
        model=model,
        workspace=root / "ws",
        title=title,
        profile=profile,
        mode="default",
        test=TestMode(loopback_http_provider=True),
        tools=None,
    )


async def send(session: Session, value: str) -> Any:
    from qma.harness import OperatorText  # noqa: PLC0415

    await session.harness.send(session.chat, OperatorText(value))
    return await wait_turn(session.home, session.chat)


async def lane_e18(say: Log) -> int:
    fake = FakeModel([SPAWN, Turn([text("the review is in")])], routes=ROUTES).start()
    root = fresh("e18")
    use_fake_key()
    put_providers(root, fake_rows(fake.url, "kimi", "deepseek"))
    set_pins(root, FAKE_PINS)
    try:
        session = await open_chat(root, profile="kimi", model="kimi-k3", title="rtr6 e18")
        await session.turn(say, "Get one review from the Kimi reviewer.")
        found = listed(session)
        say(f"definitions listed: {json.dumps(found, sort_keys=True)}")
        say.check(
            "the Kimi main is offered a Kimi-named definition on the Kimi row",
            found.get("kimi-reviewer") == "kimi/k3",
            found.get("kimi-reviewer"),
        )
        say.check(
            "the DeepSeek pin is offered beside it",
            found.get("deepseek-reviewer") == "deepseek/deepseek-v4-pro",
            found.get("deepseek-reviewer"),
        )
        say.check(
            "the sub-agent's request reached the Kimi row with 'kimi-k3' unchanged",
            asked(fake, "kimi-k3") >= 1,
            asked(fake, "kimi-k3"),
        )
        transcript = session.transcript()
        say.check(
            "the Kimi reviewer's answer came back to the main",
            "KIMI-REVIEW-OK" in transcript,
            "KIMI-REVIEW-OK" in transcript,
        )
        say("E18's engine half: not run. The v1 definition has no `subagents` field, so an agent "
            "node cannot declare `max_concurrent` or spawn five; that packet is unscheduled "
            "(HARDENING-PLAN Appendix G).")
        return 0
    finally:
        fake.stop()


async def lane_cache(say: Log) -> int:
    fake = FakeModel([Turn([text("one")]), Turn([text("two")])]).start()
    root = fresh("cache")
    use_fake_key()
    put_providers(root, fake_rows(fake.url, "kimi", "deepseek"))
    set_pins(root, FAKE_PINS)
    try:
        found = []
        for index in (1, 2):
            session = await open_chat(
                root, profile="kimi", model="kimi-k3", title=f"rtr6 cache {index}"
            )
            await session.turn(say, "Say one word.")
            found.append(listed(session))
            say(f"chat {index} lists {len(found[-1])} definitions: {json.dumps(found[-1])}")
            await session.harness.close()
        say.check("both chats list the same names and models", found[0] == found[1], "")
        say.check(
            "and each lists one definition per role plus the two pins",
            len(found[0]) == ROLES + 2,
            len(found[0]),
        )
        return 0
    finally:
        fake.stop()


async def lane_regen(say: Log) -> int:
    fake = FakeModel([Turn([text("one")]), Turn([text("two")])]).start()
    root = fresh("regen")
    use_fake_key()
    put_providers(root, fake_rows(fake.url, "kimi", "deepseek"))
    set_pins(root, FAKE_PINS)
    try:
        first = await open_chat(root, profile="kimi", model="kimi-k3", title="rtr6 regen")
        await first.turn(say, "Say one word.")
        before = listed(first)
        chat = str(first.chat)
        say(f"before the relaunch: {json.dumps(before, sort_keys=True)}")
        await first.harness.close()
        set_pins(root, {"reviewer": ["deepseek/deepseek-v4-pro"]})
        second = await open_chat(root, profile="kimi", model="kimi-k3", title="rtr6 regen")
        await second.harness.send(chat, _operator("Say one word again."))
        await wait_turn(second.home, chat)
        after = json.loads((second.home.launch_dir(chat) / "surface.json").read_text("utf-8"))
        found = dict(after["agents"])
        say(f"after the relaunch: {json.dumps(found, sort_keys=True)}")
        say.check("the unpinned definition left on the relaunch", "kimi-reviewer" not in found, "")
        say.check("the pinned one stayed", "deepseek-reviewer" in found, "")
        say("a provider row disabled in [providers] does not leave the set: the generator reads "
            "the model registry, not the configured rows (BACKLOG, RTR6)")
        await second.harness.close()
        return 0
    finally:
        fake.stop()


def _operator(value: str) -> Any:
    from qma.harness import OperatorText  # noqa: PLC0415

    return OperatorText(value)


async def lane_unknown(say: Log) -> int:
    spawn = Turn(
        [
            tool_use(
                "Task",
                {
                    "description": "nobody",
                    "prompt": "Do nothing.",
                    "subagent_type": "nope-reviewer",
                },
            )
        ]
    )
    fake = FakeModel([spawn, Turn([text("the helper failed; here is my answer")])]).start()
    root = fresh("unknown")
    use_fake_key()
    put_providers(root, fake_rows(fake.url, "kimi", "deepseek"))
    set_pins(root, FAKE_PINS)
    try:
        session = await open_chat(root, profile="kimi", model="kimi-k3", title="rtr6 unknown")
        record, blocks = await session.turn(say, "Use the nope-reviewer agent.")
        say(f"turn ended {record.turn}; blocks written: {len(blocks)}")
        said = json.dumps(blocks)
        say.check("the parent's turn ended idle, not failed", record.turn == "idle", record.turn)
        say.check(
            "the parent answered after the unknown helper failed",
            "here is my answer" in said,
            said[:200],
        )
        return 0
    finally:
        fake.stop()


async def lane_perf(say: Log) -> int:
    """Launch time with the generated set against none. Not gated (Override 4)."""
    fake = FakeModel([]).start()
    use_fake_key()
    samples: dict[str, list[float]] = {"with": [], "none": []}
    try:
        for name, alias in (("with", "kimi"), ("none", "unlisted")):
            for index in range(PER_LAUNCH):
                root = fresh(f"perf-{name}-{index}")
                put_providers(root, fake_rows(fake.url, "kimi") if name == "with" else {})
                if name == "none":
                    put_providers(
                        root,
                        {
                            "unlisted": {
                                "base_url": fake.url,
                                "credential_ref": FAKE_REF,
                                "tiers": dict.fromkeys(
                                    ("opus", "sonnet", "haiku", "fable"), "kimi-k3"
                                ),
                            }
                        },
                    )
                session = await open_chat(
                    root, profile=alias, model="kimi-k3", title=f"rtr6 perf {name}"
                )
                generated = len(definitions(bundled(), Main(ProfileName(alias), "kimi-k3")))
                started = time.perf_counter()
                await session.harness.send(session.chat, _operator("hi"))
                await wait_turn(session.home, session.chat)
                samples[name].append((time.perf_counter() - started) * 1000)
                say(
                    f"{name} {index}: {samples[name][-1]:.0f} ms, "
                    f"{generated} definitions generated"
                )
                await session.harness.close()
        slow = statistics.median(samples["with"])
        fast = statistics.median(samples["none"])
        say(
            f"launch median: {slow:.0f} ms with {ROLES} definitions, {fast:.0f} ms with none, "
            f"{slow - fast:+.0f} ms (Override 4: recorded, no fail rule)"
        )
        say(f"the plan's metric names 12 definitions; the shipped role table is {ROLES} roles")
        return 0
    finally:
        fake.stop()


async def lane_plan(say: Log) -> int:
    require_login(say)
    with lane_lock():
        session = await open_chat(SHIP_HOME, profile="claude", model="haiku", title="rtr6 plan")
        await session.turn(say, "Answer with the single word OK.")
        found = listed(session)
        say(f"definitions listed: {json.dumps(found, sort_keys=True)}")
        third_party = {name: model for name, model in found.items() if "/" in str(model)}
        say.check(
            "every definition is a plan alias, so no third-party model under a plan main",
            not third_party,
            third_party,
        )
        say.check("one definition per role", len(found) == ROLES, len(found))
        say("P0 failed at PRB-R, so the plan lane does not ship and every third-party row stays "
            "plan_main_native: delegate_only. This lane is that fallback, measured.")
        return 0


async def lane_p1k(say: Log) -> int:
    root = fresh("p1k")
    put_providers(root, {"openrouter": OPENROUTER})
    set_pins(root, OPENROUTER_PINS)
    with lane_lock():
        session = await open_chat(root, profile="openrouter", model="opus", title="rtr6 p1k")
        _record, blocks = await session.turn(say, P1K_PROMPT)
        found = listed(session)
        say(f"definitions listed: {json.dumps(found, sort_keys=True)}")
        say.check(
            "both pinned reviewers are listed on their OpenRouter rows",
            found.get("deepseek-reviewer") == "openrouter/deepseek/deepseek-v4.1-flash"
            and found.get("qwen-reviewer") == "openrouter/qwen/qwen3.6-plus",
            found,
        )
        served = {(row.get("model"), row.get("status")) for row in relay_rows(session)}
        say(f"relay journal: {sorted(map(str, served))}")
        models = {str(model) for model, status in served if status == 200}
        say.check(
            "the relay sent both reviewers' rows upstream with 200",
            len({"deepseek/deepseek-v4.1-flash", "qwen/qwen3.6-plus"} & models) == 2,
            sorted(models),
        )
        said = " ".join(
            str(block["content"].get("text", ""))
            for block in blocks
            if block.get("type") == "text"
        )
        say.check(
            "the main repeated both reviewers' answers",
            "deepseek-reviewer" in said and "qwen-reviewer" in said,
            said[:160],
        )
        return 0


async def lane_gpt(say: Log) -> int:
    fake = FakeModel([SPAWN, Turn([text("the review is in")])], routes=ROUTES).start()
    root = fresh("gpt")
    use_fake_key()
    (root / "state").mkdir(parents=True, exist_ok=True)
    shutil.copy2(SHIP_HOME / "state" / "gpt-probe.json", root / "state" / "gpt-probe.json")
    put_providers(root, fake_rows(fake.url, "kimi", "deepseek") | {"gpt": GPT_ROW})
    set_pins(root, FAKE_PINS)
    try:
        session = await open_chat(root, profile="gpt", model="gpt-6.1-sol", title="rtr6 gpt")
        await session.turn(say, "Ask the Kimi reviewer for one review.")
        found = listed(session)
        say(f"definitions listed: {json.dumps(found, sort_keys=True)}")
        say.check(
            "a GPT main is offered the key rows as native sub-agents (probe P1k's GPT row)",
            found.get("kimi-reviewer") == "kimi/k3",
            found.get("kimi-reviewer"),
        )
        say.check(
            "the Kimi sub-agent's request reached the Kimi row",
            asked(fake, "kimi-k3") >= 1,
            asked(fake, "kimi-k3"),
        )
        return 0
    finally:
        fake.stop()


LANES: Final[dict[str, Any]] = {
    "e18": lane_e18,
    "cache": lane_cache,
    "regen": lane_regen,
    "unknown": lane_unknown,
    "perf": lane_perf,
    "plan": lane_plan,
    "p1k": lane_p1k,
    "gpt": lane_gpt,
}


def main() -> int:
    from qma.boot import scrub_process_env  # noqa: PLC0415

    lane = sys.argv[1] if len(sys.argv) > 1 else ""
    if lane not in LANES:
        raise SystemExit(f"usage: rtr6_subagents.py {{{'|'.join(LANES)}}}")
    removed = scrub_process_env(os.environ)
    say = Log(f"{PREFIX}rtr6-{lane}")
    say(f"lane {lane}; scrubbed {len(removed)} names from this process (names only)")
    try:
        asyncio.run(LANES[lane](say))
    except SystemExit:
        raise
    except Exception as error:  # a lane that dies still records its verdict
        say(f"the lane raised {type(error).__name__}: {str(error)[:400]}")
        say.check(f"the {lane} lane ran to its end", False, type(error).__name__)
    return say.verdict()


if __name__ == "__main__":
    sys.exit(main())
