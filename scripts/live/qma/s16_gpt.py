"""S16, the GPT lane behind the probe (HARNESS-PLAN HP16 lanes 1 to 7 and the perf probe), in one
process on the QMX home, through the operator's stored ChatGPT sign-in (keyring `qmx/chatgpt`).

    probe     Removes any stored probe result, then `Harness.gpt_login(sign_in=False)`: the
              stored sign-in, the gpt row, probes P0 to P7, the lane. `<p>hp16-p6.log` passes
              on P6's Bash call; `<p>hp16-p7.log` on P7 and a stored `ProbePassed`.
    spent     The probe grant P6 and P7 used, sent again. `<p>hp16-spent.log`: 401.
    consent   Background consent off: a direct unattended grant raises `GrantRefused` and a
              Background GPT chat's send is refused; consent on: the same chat runs a turn. The
              stored answer is put back. `<p>hp16-consent.log`.
    toolsearch  The GPT CLI's init tool list and env from that Background launch.
              `<p>hp16-toolsearch.log`: no ToolSearch, ENABLE_TOOL_SEARCH=false.
    nopass    The stored pass moved aside: `start_chat` on gpt is refused and the lane closes;
              the pass is put back. `<p>hp16-nopass.log`.
    changed   One byte appended to `translate.py`: the stored result reads as None; the file
              is put back byte for byte. `<p>hp16-changed.log`.
    perf      Five hellos through the lane, `--spacing` seconds apart, timed to the first
              streamed byte. `<p>hp16-perf.log`: median within 500 ms of HP2's 2.70 s.
    console   With --only ...,console, this process's harness is served on port 8876 and
              `op_checks_console.py 10` runs against it (`--video` records it): one host and
              one sign-in for the whole run. `<p>hp16-check10.log`, `hp16-check10.png`,
              `hp16-usage.png`.
    secrets   Every ChatGPT token value this process held, searched for in the evidence folder,
              the home and the scratch folders. `<p>hp16-s16-secrets.log`.

The sign-in is never opened in a browser here. If the stored sign-in does not refresh, the
script logs OPERATOR-PENDING and exits 3. No token value is printed or written.

    s16_gpt.py [--home <qmx home>] [--prefix owner-] [--perf-runs 5] [--spacing 60]
               [--only lanes,perf,console] [--video]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import statistics
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
from common import (
    SCRATCH,
    SHIP_HOME,
    Log,
    boot,
    capture_launches,
    files_holding,
    session_blocks,
    show,
    use_fake_home,
    wait_turn,
)

HP2_MEDIAN_S = 2.70
PERF_MARGIN_S = 0.5
HELLO = {
    "model": "opus",
    "max_tokens": 64,
    "stream": True,
    "messages": [{"role": "user", "content": "Say exactly: hello from QMA"}],
}
WORKSPACE = SCRATCH / "hp16-ws"
PORT = 8876
UI_ORIGIN = "http://127.0.0.1:5173"


def refuse_page(url: str) -> None:
    raise SystemExit("s16_gpt.py never opens the ChatGPT sign-in page")


def capture_probe_grants() -> list[Any]:
    from qma.harness.relay import Relay  # noqa: PLC0415

    minted: list[Any] = []
    original = Relay.probe_grant

    async def probe_grant(self: Relay, *args: Any, **kwargs: Any) -> Any:
        found = await original(self, *args, **kwargs)
        minted.append(found)
        return found

    Relay.probe_grant = probe_grant
    return minted


async def post(base_url: str, secret: str, body: dict[str, Any]) -> tuple[int, str]:
    headers = {"authorization": f"Bearer {secret}", "anthropic-version": "2023-06-01"}
    async with httpx.AsyncClient(base_url=base_url, trust_env=False, timeout=120) as client:
        reply = await client.post("/v1/messages", json=body, headers=headers)
        return reply.status_code, reply.text[:300]


async def first_byte(base_url: str, secret: str) -> tuple[float | None, str]:
    """Seconds from sending a streamed hello to its first body byte, and the whole reply."""
    headers = {"authorization": f"Bearer {secret}", "anthropic-version": "2023-06-01"}
    started = time.perf_counter()
    first: float | None = None
    body = b""
    async with (
        httpx.AsyncClient(base_url=base_url, trust_env=False, timeout=120) as client,
        client.stream("POST", "/v1/messages", json=HELLO, headers=headers) as reply,
    ):
        async for chunk in reply.aiter_bytes():
            if first is None and chunk:
                first = time.perf_counter() - started
            body += chunk
    return first, body.decode(errors="replace")


async def run(args: argparse.Namespace) -> int:
    from qma.gpt import probe, translate  # noqa: PLC0415
    from qma.harness import (  # noqa: PLC0415
        Harness,
        InjectedText,
        LaunchRefused,
        NewChat,
        QmxHome,
        SessionId,
    )
    from qma.harness.harness import open_gpt_lane  # noqa: PLC0415
    from qma.harness.launch import Background  # noqa: PLC0415
    from qma.harness.profiles import ProfileName  # noqa: PLC0415
    from qma.harness.relay import GrantRefused  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    p = args.prefix
    home = QmxHome(args.home)
    control = control_service(home)
    grants = capture_probe_grants()
    launched = capture_launches()
    harness = await Harness.open(home, control=control)
    relay = harness._deps.relay  # pyright: ignore[reportPrivateUsage]
    state = home.state_dir
    verdicts: list[int] = []
    try:
        if "lanes" in args.only:
            (state / probe.PROBE_FILE).unlink(missing_ok=True)
            p6, p7 = Log(f"{p}hp16-p6"), Log(f"{p}hp16-p7")
            status = await harness.gpt_login(sign_in=False, open_page=refuse_page)
            for line in status.lines:
                p6(line)
                p7(line)
            if status.needs_sign_in:
                for log in (p6, p7):
                    log(
                        "OPERATOR-PENDING: the stored ChatGPT sign-in did not refresh; "
                        "/login chatgpt"
                    )
                return 3
            p6.check(
                "P6: the bundled CLI ran a Bash call through the GPT lane and the turn completed",
                any(line.startswith("P6 PASS") for line in status.lines),
                next((line for line in status.lines if line.startswith("P6")), "no P6 line"),
            )
            stored = probe.stored_result(state, probe.translator_version())
            p7.check(
                "P7: ClaudeSDKClient on the GPT route completed its Bash turn",
                any(line.startswith("P7 PASS") for line in status.lines),
                next((line for line in status.lines if line.startswith("P7")), "no P7 line"),
            )
            p7.check(
                "a ProbePassed is stored for this translator version",
                isinstance(stored, probe.ProbePassed),
                stored,
            )
            p7.check("the GPT lane is open", relay.gpt is not None, relay.gpt is not None)
            verdicts += [p6.verdict(), p7.verdict()]
            if relay.gpt is None:
                return 1

            spent = Log(f"{p}hp16-spent")
            spent(f"probe grants minted this run: {len(grants)}")
            code, text = await post(relay.base_url, grants[-1].secret, HELLO)
            spent(f"reply: {code} {text}")
            spent.check("the spent probe grant gets 401", code == 401, code)
            verdicts.append(spent.verdict())

            session = relay.siwc
            consent = Log(f"{p}hp16-consent")
            original = session.background_consent
            consent(f"stored background consent before: {original}")
            WORKSPACE.mkdir(parents=True, exist_ok=True)
            try:
                await session.set_background_consent(False)
                try:
                    await relay.grant(
                        SessionId(str(uuid.uuid4())), ProfileName("gpt"), unattended=True
                    )
                    refused = "no refusal"
                except GrantRefused as error:
                    refused = str(error)
                consent.check(
                    "an unattended GPT grant without consent raises GrantRefused",
                    "consent" in refused,
                    refused,
                )
                chat = await harness.start_chat(
                    NewChat(
                        title="hp16 background",
                        model="opus",
                        profile="gpt",
                        kind=Background(),
                        workspace=WORKSPACE,
                    )
                )
                prompt = InjectedText("Reply with the single word: ok")
                try:
                    await harness.send(chat, prompt)
                    blocked = "sent"
                except LaunchRefused as error:
                    blocked = str(error)
                consent.check(
                    "the Background GPT chat is refused without consent",
                    "consent" in blocked,
                    blocked,
                )
                await session.set_background_consent(True)
                consent("consent on; sending the same prompt again")
                await harness.send(chat, prompt)
                record = await wait_turn(home, chat)
                found = session_blocks(control, chat)
                for block in found:
                    show(consent, block)
                texts = [b for b in found if b["type"] == "text" and b["content"].get("text")]
                consent.check(
                    "with consent the Background GPT chat ran its turn to the end",
                    record is not None and record.turn == "idle" and record.started and bool(texts),
                    f"turn={getattr(record, 'turn', None)} "
                    f"started={getattr(record, 'started', None)} "
                    f"text blocks={len(texts)}",
                )
            finally:
                await session.set_background_consent(original)
                consent(f"stored background consent put back to {original}")
            verdicts.append(consent.verdict())

            tools = Log(f"{p}hp16-toolsearch")
            gpt_launches = [
                client
                for client in launched
                if client.options.env.get("ANTHROPIC_BASE_URL") == relay.base_url
            ]
            tools(f"GPT chat launches captured: {len(gpt_launches)}")
            init = next(
                (
                    m.data
                    for client in gpt_launches
                    for m in client.seen
                    if getattr(m, "subtype", "") == "init"
                ),
                {},
            )
            names = list(init.get("tools", []))
            tools(f"init tools ({len(names)}): {names}")
            env = gpt_launches[-1].options.env if gpt_launches else {}
            tools(f"ENABLE_TOOL_SEARCH={env.get('ENABLE_TOOL_SEARCH')}")
            tools.check("the init tool list was read", bool(names), len(names))
            tools.check(
                "tool search is off in the GPT CLI",
                not any("toolsearch" in name.lower().replace("_", "") for name in names)
                and env.get("ENABLE_TOOL_SEARCH") == "false",
                [name for name in names if "search" in name.lower()],
            )
            verdicts.append(tools.verdict())

            nopass = Log(f"{p}hp16-nopass")
            stored_file = state / probe.PROBE_FILE
            aside = state / "gpt-probe.hp16-aside"
            shutil.move(stored_file, aside)
            try:
                try:
                    await harness.start_chat(
                        NewChat(title="hp16 no pass", profile="gpt", model="opus")
                    )
                    answer = "started"
                except LaunchRefused as error:
                    answer = str(error)
                nopass(f"start_chat on gpt with no stored pass: {answer}")
                nopass.check(
                    "start_chat is refused", answer.startswith("GPT needs a passed"), answer
                )
                nopass.check("the lane closed", relay.gpt is None, relay.gpt is None)
            finally:
                shutil.move(aside, stored_file)
                nopass(f"stored pass put back: {stored_file.exists()}")
            verdicts.append(nopass.verdict())

            changed = Log(f"{p}hp16-changed")
            source = Path(translate.__file__)
            original_bytes = source.read_bytes()
            before = probe.translator_version()
            try:
                source.write_bytes(original_bytes + b"\n")
                after = probe.translator_version()
                read = probe.stored_result(state, after)
                changed(f"translator version {before} -> {after} after one byte")
                changed.check("the stored result reads as None", read is None, read)
            finally:
                source.write_bytes(original_bytes)
            restored = probe.stored_result(state, probe.translator_version())
            changed.check(
                "translate.py is back byte for byte and the pass reads again",
                source.read_bytes() == original_bytes and isinstance(restored, probe.ProbePassed),
                probe.translator_version(),
            )
            reason = await open_gpt_lane(relay, home)
            changed(f"lane reopened from the stored pass: {reason or 'open'}")
            verdicts.append(changed.verdict())

        if "perf" in args.only and args.perf_runs:
            perf = Log(f"{p}hp16-perf")
            perf(f"baseline: HP2 direct P2 median {HP2_MEDIAN_S:.2f} s (FINDINGS.md, HP2)")
            samples: list[float] = []
            for index in range(args.perf_runs):
                if index:
                    await asyncio.sleep(args.spacing)
                grant = await relay.grant(SessionId(str(uuid.uuid4())), ProfileName("gpt"))
                try:
                    seconds, text = await first_byte(relay.base_url, grant.secret)
                finally:
                    await relay.revoke(grant)
                done = "message_stop" in text
                perf(f"run {index + 1}: first_byte_s={seconds} completed={done}")
                if seconds is not None and done:
                    samples.append(seconds)
            perf.check("every run completed", len(samples) == args.perf_runs, len(samples))
            if samples:
                median = statistics.median(samples)
                limit = HP2_MEDIAN_S + PERF_MARGIN_S
                perf(f"median_first_byte_s: {median:.3f} limit_s: {limit:.2f}")
                perf.check("median within 500 ms of HP2's", median <= limit, f"{median:.3f}")
            verdicts.append(perf.verdict())

        if "console" in args.only:
            verdicts.append(await console_lane(harness, home, control, args))
    finally:
        secrets = Log(f"{p}hp16-s16-secrets")
        values = sorted(relay.siwc.seen) if relay.siwc is not None else []
        roots = [Path(args.evidence), Path(args.home), SCRATCH]
        roots = [root for root in roots if root.exists()]
        secrets(f"token values held by this process: {len(values)}; searching {roots}")
        holders = sorted({str(path) for value in values for path in files_holding(roots, value)})
        secrets.check("no file holds a ChatGPT token value", not holders, holders)
        verdicts.append(secrets.verdict())
        await harness.close()
    return max(verdicts, default=1)


async def console_lane(harness: Any, home: Any, control: Any, args: argparse.Namespace) -> int:
    """Serve this process's harness on `PORT`, as `qma.serve` would, and run console lane 10
    against it. One host, one ChatGPT sign-in: a second process would have to refresh the
    token, which OpenAI allows only near the end of the token's hour."""
    import contextlib  # noqa: PLC0415

    import uvicorn  # noqa: PLC0415
    from qma.harness.routes import chat_router, router  # noqa: PLC0415
    from qmx_control.server import create_app, local_token  # noqa: PLC0415

    class Server(uvicorn.Server):
        @contextlib.contextmanager
        def capture_signals(self) -> Any:
            yield

    extra = router(
        home, control, scrubbed=(), keep=(), harness_lines=lambda probe: harness.doctor(probe=probe)
    )
    app = create_app(control, local_token(), UI_ORIGIN, extra_routers=[extra, chat_router(harness)])
    server = Server(uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning"))
    serving = asyncio.create_task(server.serve())
    while not server.started:
        if serving.done():
            serving.result()
        await asyncio.sleep(0.1)
    try:
        lane = await asyncio.create_subprocess_exec(
            sys.executable,
            "op_checks_console.py",
            "10",
            *(["--video"] if args.video else []),
            "--log",
            args.prefix.rstrip("-"),
            cwd=Path(__file__).parent,
            env={**os.environ, "QMA_EVIDENCE_DIR": args.evidence},
        )
        return await lane.wait()
    finally:
        server.should_exit = True
        await serving


def main() -> int:
    parser = argparse.ArgumentParser(prog="s16_gpt.py")
    parser.add_argument("--home", type=Path, default=SHIP_HOME)
    parser.add_argument("--prefix", default="owner-")
    parser.add_argument("--perf-runs", type=int, default=5)
    parser.add_argument("--spacing", type=float, default=60.0)
    parser.add_argument(
        "--only",
        type=lambda text: set(text.split(",")),
        default={"lanes", "perf"},
        help="comma list of lanes, perf, console (default lanes,perf)",
    )
    parser.add_argument("--video", action="store_true", help="record lane 10 for the review")
    args = parser.parse_args()
    args.evidence = os.environ.get("QMA_EVIDENCE_DIR", "")
    boot()
    use_fake_home()
    print(json.dumps({"home": str(args.home)}))
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
