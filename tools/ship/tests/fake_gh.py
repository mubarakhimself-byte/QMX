"""A stand-in for the `gh` calls the scripts make, run as a real subprocess.

PRs live in fake-gh.json in the git dir; each PR's head sha is read from the real remote with
`git ls-remote`. Actions runs live in fake-gh-runs.json: {"runs": [{databaseId, headSha, headBranch,
event, status, conclusion, displayTitle, url, createdAt, jobs: [...], artifacts: {name: {path: text}}}]}.
Every call is appended to fake-gh-calls.jsonl. A file fake-gh-down makes every call fail the way gh
does without a network. A file fake-gh-account makes `auth status` report that account as active.
A `-R <slug>` anywhere in the arguments is accepted and ignored."""

import json
import subprocess
import sys
from pathlib import Path


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def opt(args: list[str], name: str, default: str | None = None) -> str | None:
    return args[args.index(name) + 1] if name in args else default


def main(argv: list[str]) -> int:
    home = Path(git("rev-parse", "--git-common-dir")).resolve()
    with open(home / "fake-gh-calls.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(argv) + "\n")
    if (home / "fake-gh-down").exists():
        print("error connecting to api.github.com", file=sys.stderr)
        return 1
    if "-R" in argv:
        i = argv.index("-R")
        argv = argv[:i] + argv[i + 2:]
    if argv[:2] == ["auth", "status"] and (home / "fake-gh-account").exists():
        name = (home / "fake-gh-account").read_text("utf-8").strip()
        print(f"github.com\n  Logged in to github.com account {name} (keyring)\n  - Active account: true")
        return 0
    if argv[:1] == ["pr"]:
        return pr(home, argv)
    if argv[:1] in (["run"], ["workflow"]):
        return actions(home, argv)
    print(f"fake gh: unsupported {argv}", file=sys.stderr)
    return 2


def pr(home: Path, argv: list[str]) -> int:
    store = home / "fake-gh.json"
    prs = json.loads(store.read_text("utf-8")) if store.exists() else []
    if argv[:2] == ["pr", "create"]:
        url = f"https://github.test/pr/{len(prs) + 1}"
        prs.append({"url": url, "number": len(prs) + 1, "baseRefName": opt(argv, "--base"),
                    "head": opt(argv, "--head"), "title": opt(argv, "--title"),
                    "body": Path(opt(argv, "--body-file")).read_text("utf-8"), "state": "OPEN"})
        store.write_text(json.dumps(prs), "utf-8")
        print(url)
        return 0
    if argv[:2] == ["pr", "list"]:
        head, base = opt(argv, "--head"), opt(argv, "--base")
        rows = [p for p in prs if p["head"] == head and p["state"] == "OPEN"
                and (base is None or p["baseRefName"] == base)]
        print(json.dumps([{**p, "headRefOid": head_sha(p["head"])} for p in rows]))
        return 0
    if argv[:2] == ["pr", "view"]:
        found = next(p for p in prs if p["url"] == argv[2])
        print(json.dumps({**found, "headRefOid": head_sha(found["head"])}))
        return 0
    if argv[:2] == ["pr", "close"]:
        for p in prs:
            if p["url"] == argv[2]:
                p["state"] = "CLOSED"
        store.write_text(json.dumps(prs), "utf-8")
        return 0
    print(f"fake gh: unsupported {argv}", file=sys.stderr)
    return 2


def actions(home: Path, argv: list[str]) -> int:
    store = home / "fake-gh-runs.json"
    data = json.loads(store.read_text("utf-8")) if store.exists() else {"runs": []}
    runs = data["runs"]
    if argv[:2] == ["workflow", "run"]:
        branch = opt(argv, "--ref")
        level = opt(argv, "-f", "level=deep").split("=", 1)[1]
        new_id = max([r["databaseId"] for r in runs] + [1000]) + 1
        runs.insert(0, {"databaseId": new_id, "headSha": head_sha(branch), "headBranch": branch,
                        "event": "workflow_dispatch", "status": "queued", "conclusion": "",
                        "displayTitle": f"{level} {branch}", "url": f"https://github.test/runs/{new_id}",
                        "createdAt": "2026-11-13T00:00:00Z", "jobs": [], "artifacts": {}})
        store.write_text(json.dumps(data), "utf-8")
        return 0
    if argv[:2] == ["run", "list"]:
        branch, event, commit = opt(argv, "--branch"), opt(argv, "--event"), opt(argv, "--commit")
        rows = [r for r in runs if r["headBranch"] == branch and (event is None or r["event"] == event)
                and (commit is None or r["headSha"] == commit)]
        print(json.dumps([{k: v for k, v in r.items() if k not in ("jobs", "artifacts")} for r in rows]))
        return 0
    if argv[:2] == ["run", "view"]:
        found = next((r for r in runs if str(r["databaseId"]) == argv[2]), None)
        if found is None:
            print(f"could not find any workflow run with ID {argv[2]}", file=sys.stderr)
            return 1
        print(json.dumps({k: v for k, v in found.items() if k != "artifacts"}))
        return 0
    if argv[:2] == ["run", "download"]:
        found = next(r for r in runs if str(r["databaseId"]) == argv[2])
        files = found["artifacts"].get(opt(argv, "-n"))
        if files is None:
            print("no artifact matches any of the names or patterns provided", file=sys.stderr)
            return 1
        for rel, text in files.items():
            path = Path(opt(argv, "-D")) / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, "utf-8")
        return 0
    if argv[:2] == ["run", "rerun"]:
        found = next(r for r in runs if str(r["databaseId"]) == argv[2])
        for job in found["jobs"]:
            if str(job["databaseId"]) == opt(argv, "--job"):
                job.update({"status": "queued", "conclusion": "", "databaseId": job["databaseId"] + 1})
        store.write_text(json.dumps(data), "utf-8")
        return 0
    print(f"fake gh: unsupported {argv}", file=sys.stderr)
    return 2


def head_sha(branch: str) -> str:
    out = git("ls-remote", "origin", f"refs/heads/{branch}")
    return out.split()[0] if out else ""


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
