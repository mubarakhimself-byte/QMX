"""P0 (SOLUTION-DESIGN 26.14): first-party parity behind a base URL, under the plan login.

The same haiku turn with one `qmx` MCP tool call runs under the ship home's plan login twice per
repeat: run A with no base URL, run B with `ANTHROPIC_BASE_URL` on `router.py` and the router's
grant in `ANTHROPIC_CUSTOM_HEADERS`. Both runs go through `InterceptProxy` as `HTTPS_PROXY`, so
the requests run A sends straight to `api.anthropic.com` are recorded too, and the only launch
difference between A and B is the base URL and the grant header.

Each `/v1/messages` request of A is paired with B's and compared on the method, the path, every
header name and value in order, the top-level field order and every body field. Excluded, as
P0 names them: `host`, `content-length`, `x-qmx-grant`, and the values of per-request ids
(`x-claude-code-session-id`, request ids, `metadata.user_id`, tool-use and message ids). The
model's own words in earlier assistant turns are masked too, because they are the model's
output and not something a router or launch can change. Credential values are compared in
memory and written only as `same` or `different`.

If a difference appears, the round reruns with each env candidate in turn, set on run B's
launch only, and records which one made the pairs equal. PASS when one round's pairs are all
equal and every turn in it succeeded.

    uv run --no-sync python ../scripts/probes/router/p0_parity.py [--repeats N]
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import os
import re
import secrets
import shutil
import statistics
import sys
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Final

from common import (
    FIRST_PARTY,
    HOMES,
    TOOL_SEARCH,
    evidence,
    lane_lock,
    log,
    plan_env,
    plan_options,
    qmx_server,
    run_session,
    scrub_process_env,
)
from router import (
    ANTHROPIC_HOST,
    ANTHROPIC_URL,
    SECRET_HEADERS,
    Exchange,
    InterceptProxy,
    Recorder,
    Router,
    Upstream,
    compare_secret,
)

PROMPT: Final = (
    'Call the tool mcp__qmx__ping exactly once with word "parity". '
    "Then reply with only the text the tool returned."
)
EXPECTED: Final = "PONG-PARITY"
SKIPPED_HEADERS: Final = frozenset({"host", "content-length", "x-qmx-grant"})
PER_REQUEST_HEADERS: Final = frozenset({"x-claude-code-session-id", "x-client-request-id"})
PER_REQUEST_VALUE_HEADERS: Final = frozenset(
    {"x-claude-code-prompt-id", "x-claude-code-prev-tool-durations"}
)
"""Present on every request of a prompt, with a value per prompt or per measured duration."""
ID_SHAPE: Final = re.compile(r"^(toolu_|msg_|srvtoolu_|req_)[A-Za-z0-9_-]+$")
BILLING_IDS: Final = re.compile(r"\b(cch|cc_prompt_id|cc_prev_req)=[^;]+")
"""The per-request hash, prompt id and previous request id inside the billing line."""
TOKENS_LEFT: Final = re.compile(r"<total_tokens>\d+ tokens left</total_tokens>")
"""The CLI's running token count in a reminder; it follows the model's earlier output."""
ROUNDS: Final[list[dict[str, str]]] = [
    {},
    TOOL_SEARCH,
    TOOL_SEARCH | FIRST_PARTY,
    TOOL_SEARCH | FIRST_PARTY | {"CLAUDE_CODE_GATEWAY_HINT_HEADERS": "1"},
]
"""Run B's launch env per round: none, then each candidate. Run A is always today's launch."""
RISK_MS: Final = 50.0


def tls_files(folder: Path) -> tuple[Path, Path, Path]:
    """A throwaway CA and an `api.anthropic.com` certificate it signs. Deleted after the run."""
    from cryptography import x509  # noqa: PLC0415
    from cryptography.hazmat.primitives import hashes, serialization  # noqa: PLC0415
    from cryptography.hazmat.primitives.asymmetric import ec  # noqa: PLC0415
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID  # noqa: PLC0415

    folder.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.UTC)
    span = (now - datetime.timedelta(hours=1), now + datetime.timedelta(days=1))
    ca_key, leaf_key = (
        ec.generate_private_key(ec.SECP256R1()),
        ec.generate_private_key(ec.SECP256R1()),
    )
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "PRB-R probe CA")])
    ca = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(span[0])
        .not_valid_after(span[1])
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(False, False, False, False, False, True, True, False, False),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )
    leaf = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, ANTHROPIC_HOST)]))
        .issuer_name(ca_name)
        .public_key(leaf_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(span[0])
        .not_valid_after(span[1])
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(ANTHROPIC_HOST)]), critical=False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )
    pem = serialization.Encoding.PEM
    ca_file, cert_file, key_file = folder / "ca.pem", folder / "leaf.pem", folder / "leaf.key"
    ca_file.write_bytes(ca.public_bytes(pem))
    cert_file.write_bytes(leaf.public_bytes(pem) + ca.public_bytes(pem))
    key_file.write_bytes(
        leaf_key.private_bytes(pem, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    )
    return ca_file, cert_file, key_file


def masked(value: Any, path: str = "") -> Any:
    """`value` with per-request ids and the model's own earlier words replaced by markers."""
    if isinstance(value, dict):
        if path.endswith("metadata"):
            return {
                k: "<id>" if k == "user_id" else masked(v, f"{path}.{k}") for k, v in value.items()
            }
        if path.startswith("messages") and value.get("role") == "assistant":
            return {
                "role": "assistant",
                "content": [assistant_block(b) for b in value.get("content", [])]
                if isinstance(value.get("content"), list)
                else "<model text>",
            }
        return {k: masked(v, f"{path}.{k}" if path else k) for k, v in value.items()}
    if isinstance(value, list):
        return [masked(v, f"{path}[{i}]") for i, v in enumerate(value)]
    if isinstance(value, str):
        if ID_SHAPE.match(value):
            return "<id>"
        value = BILLING_IDS.sub(r"\1=<id>", value)
        return TOKENS_LEFT.sub("<total_tokens>N</total_tokens>", value)
    return value


def assistant_block(block: Any) -> Any:
    if not isinstance(block, dict):
        return block
    kind = block.get("type")
    if kind == "text":
        return {**masked(block), "text": "<model text>"}
    if kind in ("thinking", "redacted_thinking"):
        return {"type": kind, "<masked>": True}
    return masked(block)


def body_diffs(a: Any, b: Any, path: str = "body") -> Iterator[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        if list(a) != list(b):
            yield f"{path} field order or names: A={list(a)} B={list(b)}"
        for key in a.keys() & b.keys():
            yield from body_diffs(a[key], b[key], f"{path}.{key}")
        return
    if isinstance(a, list) and isinstance(b, list):
        if path.endswith(".tools"):
            names_a = [t.get("name") for t in a if isinstance(t, dict)]
            names_b = [t.get("name") for t in b if isinstance(t, dict)]
            if names_a != names_b:
                yield f"{path} names: {only(names_a, names_b)}"
                return
        if len(a) != len(b):
            yield f"{path} length: A={len(a)} B={len(b)}"
            return
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            yield from body_diffs(x, y, f"{path}[{i}]")
        return
    if a != b:
        yield f"{path}: A={short(a)} B={short(b)}"


def only(a: list[Any], b: list[Any]) -> str:
    return (
        f"only A={[x for x in a if x not in b]} only B={[x for x in b if x not in a]} "
        f"same set, other order={sorted(map(str, a)) == sorted(map(str, b))}"
    )


def short(value: Any) -> str:
    found = json.dumps(value) if not isinstance(value, str) else repr(value)
    return found if len(found) <= 240 else found[:240] + f"...({len(found)} chars)"


def header_diffs(a: Exchange, b: Exchange) -> Iterator[str]:
    names_a = [n for n, _ in a.headers if n.lower() not in SKIPPED_HEADERS]
    names_b = [n for n, _ in b.headers if n.lower() not in SKIPPED_HEADERS]
    if names_a != names_b:
        yield f"header names in order: {only(names_a, names_b)}"
    seen: Counter[str] = Counter()
    values_b: dict[tuple[str, int], str] = {}
    counts: Counter[str] = Counter()
    for name, value in b.headers:
        values_b[(name.lower(), counts[name.lower()])] = value
        counts[name.lower()] += 1
    for name, value in a.headers:
        low = name.lower()
        index = seen[low]
        seen[low] += 1
        if low in SKIPPED_HEADERS or (low, index) not in values_b:
            continue
        if low in SECRET_HEADERS:
            verdict = compare_secret(a, b, low)
            if verdict != "same":
                yield f"header {low}: value {verdict}"
            continue
        if low in PER_REQUEST_HEADERS | PER_REQUEST_VALUE_HEADERS or "request-id" in low:
            continue
        if low == "anthropic-beta" and value != values_b[(low, index)]:
            betas_a, betas_b = value.split(","), values_b[(low, index)].split(",")
            yield f"header anthropic-beta: {only(betas_a, betas_b)}"
        elif value != values_b[(low, index)]:
            yield f"header {low}: A={short(value)} B={short(values_b[(low, index)])}"


def compare(a: Exchange, b: Exchange) -> list[str]:
    found: list[str] = []
    if (a.method, a.path) != (b.method, b.path):
        found.append(f"request line: A={a.method} {a.path} B={b.method} {b.path}")
    found += header_diffs(a, b)
    ja, jb = a.json, b.json
    if ja or jb:
        found += body_diffs(masked(ja), masked(jb))
    elif a.body != b.body:
        found.append("raw body differs")
    return found


def kind(e: Exchange) -> tuple[str, str, str | None, bool]:
    return (e.method, e.path.partition("?")[0], e.model, bool(e.json.get("tools")))


def pair(a: list[Exchange], b: list[Exchange]) -> tuple[list[tuple[Exchange, Exchange]], list[str]]:
    pairs: list[tuple[Exchange, Exchange]] = []
    left = list(b)
    unpaired: list[str] = []
    for e in a:
        match = next((x for x in left if kind(x) == kind(e)), None)
        if match is None:
            unpaired.append(f"only in A: {e.method} {e.path} model={e.model}")
            continue
        left.remove(match)
        pairs.append((e, match))
    unpaired += [f"only in B: {e.method} {e.path} model={e.model}" for e in left]
    return pairs, unpaired


def messages_requests(exchanges: list[Exchange]) -> list[Exchange]:
    return [e for e in exchanges if e.path.partition("?")[0].startswith("/v1/messages")]


async def one_run(
    label: str, env: dict[str, str], proxy: InterceptProxy, router: Router, workspace: Path
) -> Any:
    from claude_agent_sdk import ClaudeAgentOptions  # noqa: PLC0415

    proxy.recorder.run = router.recorder.run = label
    options = ClaudeAgentOptions(
        **plan_options(
            env=env,
            cwd=str(workspace),
            tools=["Read", "Glob"],
            mcp_servers={"qmx": qmx_server()},
            allowed_tools=["mcp__qmx__ping"],
        )
    )
    return await run_session(options, PROMPT)


def run_round(
    say: Any,
    index: int,
    extra: dict[str, str],
    repeats: int,
    base: dict[str, str],
    proxy: InterceptProxy,
    router: Router,
    workspace: Path,
) -> tuple[bool, bool, list[str]]:
    """`(turns all succeeded, every pair equal, differences)` for one round."""
    grant = secrets.token_urlsafe(24)
    succeeded, differences = True, []
    for rep in range(repeats):
        labels = {"A": f"r{index}-A{rep}", "B": f"r{index}-B{rep}"}
        envs = {
            "A": base,
            "B": base
            | extra
            | {
                "ANTHROPIC_BASE_URL": router.url,
                "ANTHROPIC_CUSTOM_HEADERS": f"x-qmx-grant: {grant}",
            },
        }
        for mode in ("A", "B"):
            outcome = asyncio.run(one_run(labels[mode], envs[mode], proxy, router, workspace))
            tools = [n for n, _ in outcome.tool_uses]
            ok = (
                not outcome.is_error
                and not outcome.error
                and tools == ["mcp__qmx__ping"]
                and EXPECTED in outcome.result
            )
            succeeded &= ok
            say(
                f"[round {index} {labels[mode]}] turn ok={ok} tools={tools} "
                f"result={outcome.result[:80]!r} error={outcome.error!r}"
            )
        a_all = proxy.recorder.of(labels["A"]) + router.recorder.of(labels["A"])
        b_all = proxy.recorder.of(labels["B"]) + router.recorder.of(labels["B"])
        for mode, found in (("A", a_all), ("B", b_all)):
            via = {
                e.lane + (" via router" if e in router.recorder.exchanges else " via proxy")
                for e in found
            }
            say(
                f"[round {index} {labels[mode]}] methods and paths: "
                f"{[f'{e.method} {e.path} -> {e.status}' for e in found]} lanes={sorted(via)}"
            )
        pairs, unpaired = pair(messages_requests(a_all), messages_requests(b_all))
        differences += unpaired
        others_a = sorted(
            {f"{e.method} {e.path}" for e in a_all}
            - {f"{e.method} {e.path}" for e in messages_requests(a_all)}
        )
        others_b = sorted(
            {f"{e.method} {e.path}" for e in b_all}
            - {f"{e.method} {e.path}" for e in messages_requests(b_all)}
        )
        say(f"[round {index} rep {rep}] other api.anthropic.com paths: A={others_a} B={others_b}")
        for i, (a, b) in enumerate(pairs):
            found = compare(a, b)
            verdict = f"{len(found)} differences" if found else "equal"
            say(
                f"[round {index} rep {rep}] pair {i} {a.method} {a.path} model={a.model} "
                f"tools={bool(a.json.get('tools'))}: {verdict}"
            )
            for line in found:
                say(f"    DIFF {line}")
            differences += found
            auth = compare_secret(a, b, "authorization")
            say(
                f"    authorization A vs B: {auth}; oauth-shaped in A: "
                f"{(a.header('authorization') or '').startswith('Bearer sk-ant-oat')}"
            )
    return succeeded, not differences, differences


def perf(say: Any, router: Router, proxy: InterceptProxy, label_prefix: str) -> float | None:
    b = [e for e in messages_requests(router.recorder.exchanges) if e.run.startswith(label_prefix)]
    a = [
        e
        for e in messages_requests(proxy.recorder.exchanges)
        if e.run.startswith(label_prefix.replace("-B", "-A"))
    ]
    if not b:
        return None
    overhead = statistics.median(e.overhead_ms() for e in b)
    say(
        f"PERF router overhead per plan request: median {overhead:.2f} ms over {len(b)} requests "
        f"(each {[round(e.overhead_ms(), 2) for e in b]})"
    )
    connect = statistics.median(e.connect_ms for e in b)
    say(f"PERF upstream connect+TLS per request: router median {connect:.1f} ms")
    for name, found in (("A no base URL", a), ("B router", b)):
        totals = [round((e.done_at - e.received_at) * 1000) for e in found if e.done_at]
        if totals:
            median = statistics.median(totals)
            say(f"PERF request wall time {name}: median {median} ms over {len(totals)} ({totals})")
    return overhead


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    removed = scrub_process_env(os.environ)
    say = log("p0")
    say(f"scrubbed {len(removed)} names from the process env (names only)")
    import claude_agent_sdk  # noqa: PLC0415

    say(f"claude_agent_sdk {claude_agent_sdk.__version__}; model haiku; repeats {args.repeats}")
    root = HOMES / "prb-r-p0"
    shutil.rmtree(root, ignore_errors=True)
    workspace = root / "ws"
    workspace.mkdir(parents=True)
    ca, cert, key = tls_files(root / "tls")
    base = plan_env("p0") | {"NODE_EXTRA_CA_CERTS": str(ca), "NO_PROXY": "127.0.0.1,localhost"}
    verdict_env: dict[str, str] | None = None
    succeeded_all = True
    try:
        with (
            lane_lock(say),
            InterceptProxy(cert, key) as proxy,
            Router(lambda _: Upstream("anthropic", ANTHROPIC_URL)) as router,
        ):
            base |= {"HTTPS_PROXY": proxy.url}
            say(f"proxy {proxy.url}; router {router.url}")
            say("both runs use the proxy; run B adds the base URL, the grant and the round's env")
            for index, extra in enumerate(ROUNDS):
                say(f"=== round {index}: run B launch env {extra or '(none)'}")
                succeeded, equal, differences = run_round(
                    say, index, extra, args.repeats, base, proxy, router, workspace
                )
                succeeded_all &= succeeded
                say(
                    f"round {index}: turns succeeded={succeeded}; pairs equal={equal}; "
                    f"differences={len(differences)}"
                )
                overhead = perf(say, router, proxy, f"r{index}-B")
                if overhead is not None and overhead > RISK_MS:
                    say(f"RISK router overhead median {overhead:.2f} ms is above {RISK_MS:.0f} ms")
                if equal and succeeded:
                    verdict_env = extra
                    break
            say(f"tunnelled hosts (names only): {sorted(set(proxy.recorder.tunnels))}")
            merged = Recorder()
            merged.exchanges = proxy.recorder.exchanges + router.recorder.exchanges
            merged.tunnels = proxy.recorder.tunnels
            merged.write(evidence("prb-r-p0-recording.json"))
    finally:
        shutil.rmtree(root / "tls", ignore_errors=True)
        say(f"probe TLS files removed: {not (root / 'tls').exists()}")
    passed = verdict_env is not None
    say.check(
        "P0 first-party parity: every /v1/messages pair equal outside P0's exclusions, turns green",
        passed,
        f"restoring env {verdict_env}"
        if passed
        else f"no round equal; turns all green={succeeded_all}",
    )
    return say.verdict()


if __name__ == "__main__":
    sys.exit(main())
