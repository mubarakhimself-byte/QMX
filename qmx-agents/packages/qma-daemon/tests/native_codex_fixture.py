"""Offline app-server peer for the released SDK's real transport and router.

This peer is test-only. Production uses CodexClient, never this JSONL code.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

configuration, arguments = json.loads(sys.argv[1]), json.loads(sys.argv[2])
scenario, workspace, trace = sys.argv[3], sys.argv[4], Path(sys.argv[5])
thread_id, turn_id = "sdk-thread-1", "sdk-turn-1"


def send(message: dict[str, Any]) -> None:
    print(json.dumps(message), flush=True)


def terminal(status: str = "completed") -> None:
    text = trace.with_suffix(".marker").read_text() if scenario == "proof" else "Metadata received"
    items: list[dict[str, Any]] = [{"type": "agentMessage", "id": "final-1", "text": text}]
    if scenario == "forbidden-terminal":
        items.append(
            {"type": "fileChange", "id": "forbidden-1", "changes": [], "status": "completed"}
        )
    if scenario != "no-delta":
        send(
            {
                "method": "item/agentMessage/delta",
                "params": {
                    "threadId": thread_id,
                    "turnId": turn_id,
                    "itemId": "message-1",
                    "delta": text,
                },
            }
        )
    send(
        {
            "method": "turn/completed",
            "params": {
                "threadId": "wrong-thread" if scenario == "wrong-terminal" else thread_id,
                "turn": {"id": turn_id, "status": status, "items": items},
            },
        }
    )


for line in sys.stdin:
    message = json.loads(line)
    with trace.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(message) + "\n")
    method, params, identity = message.get("method"), message.get("params", {}), message.get("id")
    result: dict[str, Any]
    if method == "initialize":
        assert params["capabilities"]["experimentalApi"]
        result = {"serverInfo": {"name": "offline-codex", "version": "0.160.0"}}
        if scenario == "wrong-initialize":
            result = {"serverInfo": {"version": "0.159.3"}, "userAgent": "codex/0.160.0 windows"}
    elif method == "config/read":
        if scenario == "withheld-config":
            continue
        actual = json.loads(json.dumps(configuration))
        if scenario == "unsafe-config":
            actual["features"]["hooks"] = True
        result = {"config": actual, "origins": {}}
    elif method == "account/read":
        result = {
            "account": {"type": "apiKey"}
            if scenario == "api-account"
            else {
                "type": "chatgpt",
                "email": None,
                "planType": "plus",
            },
            "requiresOpenaiAuth": True,
        }
    elif method in {"thread/start", "thread/resume"}:
        assert params["approvalPolicy"] == "never" and params["modelProvider"] == "openai"
        assert params["runtimeWorkspaceRoots"] == []
        if method == "thread/start":
            assert params["environments"] == []
            assert params["dynamicTools"][0]["name"] == "research_browse"
        else:
            assert params["threadId"] == thread_id and "dynamicTools" not in params
        result = {
            "approvalPolicy": "never",
            "approvalsReviewer": "user",
            "cwd": workspace,
            "model": "fixture",
            "modelProvider": "openai",
            "sandbox": {"type": "readOnly", "networkAccess": False},
            "instructionSources": [],
            "thread": {
                "id": "wrong-resume"
                if scenario == "wrong-resume" and method == "thread/resume"
                else thread_id,
                "sessionId": "cli-session-1",
                "cliVersion": "0.160.0",
                "createdAt": 1,
                "updatedAt": 1,
                "cwd": workspace,
                "ephemeral": False,
                "modelProvider": "openai",
                "preview": "fixture",
                "source": "appServer",
                "status": {"type": "idle"},
                "turns": [],
            },
        }
    elif method == "turn/start":
        assert params["environments"] == [] and params["approvalPolicy"] == "never"
        if scenario == "delayed-turn":
            time.sleep(0.2)  # Test-only protocol timing race, not a model call.
        send(
            {
                "id": identity,
                "result": {"turn": {"id": turn_id, "items": [], "status": "inProgress"}},
            }
        )
        if scenario in {"wait", "delayed-turn"}:
            continue
        if scenario == "proof":
            marker = re.search(r"NATIVE-PROOF-[a-f0-9]+", json.dumps(params["input"]))
            if marker:
                trace.with_suffix(".marker").write_text(marker.group())
            else:
                terminal()
                continue
        if scenario in {"approval", "permissions", "unknown-request"}:
            requested = {
                "approval": "item/commandExecution/requestApproval",
                "permissions": "item/permissions/requestApproval",
                "unknown-request": "future/execute",
            }[scenario]
            send(
                {
                    "id": "server-call",
                    "method": requested,
                    "params": {"threadId": thread_id, "turnId": turn_id},
                }
            )
        else:
            data = {
                "threadId": thread_id,
                "turnId": turn_id,
                "callId": "metadata-1",
                "tool": "research_browse",
                "arguments": arguments,
            }
            if scenario == "subagent":
                data["agentId"] = "native-child"
            if scenario == "wrong-tool-id":
                data["turnId"] = "another-turn"
            send({"id": "server-call", "method": "item/tool/call", "params": data})
        continue
    elif method == "turn/interrupt":
        send({"id": identity, "result": {}})
        terminal("interrupted")
        continue
    elif method is None and identity == "server-call":
        if scenario == "approval":
            assert message["result"] == {"decision": "decline"}
        elif scenario == "permissions":
            assert message["result"] == {"permissions": {}, "scope": "turn"}
        elif scenario in {"subagent", "wrong-tool-id"}:
            assert not message["result"]["success"]
        else:
            assert message["result"]["success"]
            locator = "proof.md" if scenario == "proof" else "visible.md"
            assert locator in message["result"]["contentItems"][0]["text"]
        terminal()
        continue
    else:
        continue
    send({"id": identity, "result": result})
