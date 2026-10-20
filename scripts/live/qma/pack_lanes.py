"""PACK's live lanes: the P-PL path on the real harness, a pack added mid-session, a tampered
view, and the launch cost with five packs (H43, H48, H55).

Lanes 2 to 4 and the perf block of HARDENING-PLAN PACK, run at the PR head on `haiku` through the
ship home's plan login, while the caller holds the engine lane lock
`D:/QMX-worktrees/.engine-lane-lock`. Logs go to `<QMA_EVIDENCE_DIR>/owner-pack-lanes.log`.

Lane 2. Two fixture packs materialised by `qma.harness.packs` and loaded by a real chat: both
packs' skills list, a pack agent spawns, a pack command runs, and no pack hook or MCP server runs.
Lane 3. A pack added mid-session: the chat does not relaunch for its tools, and the new pack's
skills, agents and commands list at the next turn with the earlier context kept.
Lane 4. One byte changed in one view: that pack is not loaded, the other loads, and the doctor
names the tampered one.
Perf. Chat launch time with five packs, five launches, against PRB-H's P-PL number.

    $env:QMA_EVIDENCE_DIR = "D:/QMX-worktrees/qma-ship/build/evidence/pack"
    python pack_lanes.py
"""

from __future__ import annotations

import asyncio
import shutil
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Final

from common import SHIP_HOME, Log, Session, boot, capture_launches, chat_args, require_login

FIXTURES: Final = Path(__file__).resolve().parents[3] / "scripts" / "probes" / "harness" / "fixtures"
LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
PACKS: Final = ("pack-alpha", "pack-beta")
FIVE: Final = ("pack-one", "pack-two", "pack-three", "pack-four", "pack-five")
OBJECT: Final = "fp1:sha256:"
LAUNCHES: Final = 5
AGENT_ASK: Final = (
    "Use the Agent tool once with subagent_type pack-alpha:alpha-agent and the prompt go. Then "
    "reply with exactly the text the agent returned."
)
SKILL_ASK: Final = (
    "Use the Skill tool once to load the skill pack-alpha:alpha-skill, then reply with exactly "
    "what it told you to reply with and nothing else."
)


def files_of(folder: Path) -> dict[str, bytes]:
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in folder.rglob("*")
        if path.is_file()
    }


def sources(names: tuple[str, ...]) -> list[Any]:
    """One `PackSource` per pack, from the fixture tree under its own name. A pack beyond the two
    fixtures is the alpha tree under that pack's name, which is how the five-pack perf run gets
    five distinct views."""
    from qma.harness.packs import PackSource  # noqa: PLC0415

    found = []
    for name in names:
        fixtures = FIXTURES / name if (FIXTURES / name).is_dir() else FIXTURES / "pack-alpha"
        tree = files_of(fixtures)
        if fixtures.name != name:
            short = name.split("-", 1)[1]
            tree = {path.replace("alpha", short): body for path, body in tree.items()}
            tree[".claude-plugin/plugin.json"] = (
                '{"name": "' + name + '", "version": "0.1.0"}\n'
            ).encode()
        found.append(PackSource(name, (f"{OBJECT}{name}",), tree))
    return found


def materialise(names: tuple[str, ...]) -> dict[str, Path]:
    """Write each pack's view where the ship home's chats read it, and say where it went."""
    from qma.harness.home import QmxHome  # noqa: PLC0415
    from qma.harness.packs import materialise as write  # noqa: PLC0415

    return {view.name: view.folder for view in write(QmxHome(SHIP_HOME).packs_dir, sources(names))}


def reply(blocks: list[dict[str, Any]]) -> str:
    return " ".join(
        str(block["content"].get("text", ""))
        for block in blocks
        if block["type"] in {"assistant", "result"} and block["content"].get("text")
    )


def tool_uses(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [block["content"] for block in blocks if block["type"] == "tool_use"]


async def lane_two(say: Log, root: Path) -> dict[str, Any]:
    """The P-PL path on the real harness: both packs' skills, one agent, one command."""
    folders = materialise(PACKS)
    say("materialised " + ", ".join(folders))
    session = await Session.start(
        SHIP_HOME, model="haiku", workspace=root / "ws", title="pack-ppl", tools=["Agent", "Skill"]
    )
    await session.harness.set_packs(session.chat, PACKS)
    _, command = await session.turn(say, "/pack-beta:beta-cmd")
    _, skill = await session.turn(say, SKILL_ASK)
    _, agent = await session.turn(say, AGENT_ASK)
    surface = session.harness.surface(session.chat)
    assert surface is not None
    return {
        "command": reply(command),
        "skill": reply(skill),
        "skill_calls": tool_uses(skill),
        "agent": reply(agent),
        "agent_calls": tool_uses(agent),
        "views": [view.name for view in surface.views],
        "skills": list(surface.skills),
        "plugins": [path.name for path in surface.plugins],
        "external": [name for name in surface.toolsets if name.startswith("mcp:")],
    }


async def lane_three(say: Log, root: Path) -> dict[str, Any]:
    """A pack added mid-session: tools at once, skills at the next turn, context kept."""
    import secrets  # noqa: PLC0415

    materialise(PACKS)
    word = f"KEPT-{secrets.token_hex(3).upper()}"
    launched = capture_launches()
    session = await Session.start(
        SHIP_HOME, model="haiku", workspace=root / "ws", title="pack-mid", tools=["Agent", "Skill"]
    )
    await session.harness.set_packs(session.chat, ("pack-alpha",))
    _, first = await session.turn(say, f"Remember the word {word}. Reply with the single word OK.")
    before = len(launched)
    await session.harness.set_packs(session.chat, PACKS)
    after_set = len(launched)
    _, second = await session.turn(
        say, "What word did I ask you to remember? Reply with only that word."
    )
    _, joined = await session.turn(say, "/pack-beta:beta-cmd")
    after_turn = len(launched)
    surface = session.harness.surface(session.chat)
    assert surface is not None
    return {
        "word": word,
        "first": reply(first),
        "recall": reply(second),
        "command": reply(joined),
        "launches_before_set": before,
        "launches_right_after_set": after_set,
        "launches_after_next_turn": after_turn,
        "views": [view.name for view in surface.views],
        "skills": list(surface.skills),
    }


async def lane_four(say: Log, root: Path) -> dict[str, Any]:
    """One byte changed in one view: that pack is refused, the other loads, the doctor names it."""
    from qma.harness import packs  # noqa: PLC0415
    from qma.harness.home import QmxHome, doctor  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    folders = materialise(PACKS)
    target = folders["pack-alpha"] / "skills" / "alpha-skill" / "SKILL.md"
    target.write_bytes(target.read_bytes().replace(b"ALPHA-SKILL-OK", b"ALPHA-SKILL-X"))
    home = QmxHome(SHIP_HOME)
    survey = packs.survey(home.packs_dir, PACKS)
    lines = await asyncio.to_thread(
        doctor, home, control_service(home), scrubbed=(), keep=(), launcher=Path(sys.executable)
    )
    named = [
        line.detail
        for line in lines
        if line.name.startswith("pack view ") and not line.ok and "pack-alpha" in line.detail
    ]
    session = await Session.start(
        SHIP_HOME, model="haiku", workspace=root / "ws", title="pack-tamper", tools=["Skill"]
    )
    await session.harness.set_packs(session.chat, PACKS)
    surface = session.harness.surface(session.chat)
    assert surface is not None
    return {
        "loaded": [view.name for view in survey.views],
        "refused": [name for name, _ in survey.refusals],
        "refusal": survey.refusals[0][1] if survey.refusals else "",
        "doctor_named": named,
        "surface_views": [view.name for view in surface.views],
        "alpha_skill_listed": "pack-alpha:alpha-skill" in surface.skills,
    }


async def perf(say: Log, root: Path) -> dict[str, Any]:
    """Chat launch time with five packs, five launches."""
    from qma.harness import OperatorText  # noqa: PLC0415

    materialise(FIVE)
    session = await Session.start(
        SHIP_HOME, model="haiku", workspace=root / "ws", title="pack-perf", tools=["Read"]
    )
    await session.harness.set_packs(session.chat, FIVE)
    timings: list[float] = []
    seen = None
    for _ in range(LAUNCHES):
        await session.harness.close_chat(session.chat)
        started = time.perf_counter()
        await session.harness.send(session.chat, OperatorText("Reply with OK."))
        seen = session.harness.surface(session.chat) or seen
        await session.harness.close_chat(session.chat)
        timings.append(round((time.perf_counter() - started) * 1000, 1))
    return {
        "launches_ms": timings,
        "median_ms": statistics.median(timings),
        "views": [] if seen is None else [view.name for view in seen.views],
    }


async def run(say: Log, root: Path) -> dict[str, Any]:
    return {
        "lane2": await lane_two(say, root / "ppl"),
        "lane3": await lane_three(say, root / "mid"),
        "lane4": await lane_four(say, root / "tamper"),
        "perf": await perf(say, root / "perf"),
    }


def verdict(say: Log, observation: dict[str, Any]) -> None:
    two, three = observation["lane2"], observation["lane3"]
    four, measured = observation["lane4"], observation["perf"]
    say.check(
        "lane 2, both packs' skills list and a pack skill loads",
        "ALPHA-SKILL-OK" in two["skill"] and "pack-beta:beta-skill" in two["skills"],
        {"skill": two["skill"], "packs": [n for n in two["skills"] if n.startswith("pack-")]},
    )
    say.check(
        "lane 2, a pack agent spawns",
        any(
            use["input"].get("subagent_type") == "pack-alpha:alpha-agent"
            for use in two["agent_calls"]
        )
        and "ALPHA-AGENT-OK" in two["agent"],
        {"calls": two["agent_calls"], "reply": two["agent"][-200:]},
    )
    say.check("lane 2, a pack command runs", "BETA-CMD-OK" in two["command"], two["command"])
    say.check(
        "lane 2, no pack hook and no pack MCP server runs",
        not two["external"] and {"pack-alpha", "pack-beta"} <= set(two["plugins"]),
        {"external": two["external"], "plugins": two["plugins"], "views": two["views"]},
    )
    say.check(
        "lane 3, tools at once and no relaunch before the next turn",
        three["launches_right_after_set"] == three["launches_before_set"] == 1,
        {
            "before": three["launches_before_set"],
            "right after set": three["launches_right_after_set"],
            "after the next turn": three["launches_after_next_turn"],
        },
    )
    say.check(
        "lane 3, the pack joins at the next turn and the context is kept",
        three["launches_after_next_turn"] == 2
        and three["word"] in three["recall"]
        and "BETA-CMD-OK" in three["command"]
        and "pack-beta:beta-skill" in three["skills"],
        {
            "launches": three["launches_after_next_turn"],
            "recall": three["recall"],
            "command": three["command"],
            "packs": [n for n in three["skills"] if n.startswith("pack-")],
        },
    )
    say.check(
        "lane 4, the tampered pack is not loaded and the other loads",
        four["refused"] == ["pack-alpha"]
        and four["loaded"] == ["pack-beta"]
        and not four["alpha_skill_listed"],
        {
            "refused": four["refused"],
            "loaded": four["loaded"],
            "refusal": four["refusal"],
            "surface views": four["surface_views"],
        },
    )
    say.check(
        "lane 4, the doctor names the tampered pack", bool(four["doctor_named"]), four["doctor_named"]
    )
    say(
        f"PERF launch ms with five packs, {LAUNCHES} launches: {measured['launches_ms']} "
        f"(median {measured['median_ms']}); PRB-H's P-PL baseline was 578.3 ms with two views and "
        f"592.9 ms with the core plugin alone"
    )


def main() -> int:
    args = chat_args(__doc__).parse_args()
    say = Log("pack-lanes")
    removed = boot()
    say(f"scrubbed {len(removed)} names from the process env (names only)")
    if not LOCK.is_dir():
        say(f"FAIL the caller does not hold {LOCK}; a plan lane needs it")
        return say.verdict()
    require_login(say)
    root = args.workspace
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    say(f"workspace {root}")
    plugins = SHIP_HOME / "plugins"
    existed = plugins.is_dir()
    try:
        observation = asyncio.run(run(say, root))
    finally:
        if not existed:
            shutil.rmtree(plugins, ignore_errors=True)
            say(f"removed {plugins}, which this lane created")
    say(f"observation {observation}")
    verdict(say, observation)
    return say.verdict()


if __name__ == "__main__":
    sys.exit(main())
