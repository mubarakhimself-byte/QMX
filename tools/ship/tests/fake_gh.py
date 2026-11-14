"""A stand-in for the `gh` calls the scripts make, run as a real subprocess.

PRs live in fake-gh.json in the git dir; each PR's head sha is read from the real remote with
`git ls-remote`. Actions runs live in fake-gh-runs.json: {"runs": [{databaseId, headSha, headBranch,
event, status, conclusion, displayTitle, url, createdAt, jobs: [...], artifacts: {name: {path: text}}}]}.
Every call is appended to fake-gh-calls.jsonl. A file fake-gh-down makes every call fail the way gh
does without a network. A file fake-gh-account makes `auth status` report that account as active.
A `-R <slug>` anywhere in the arguments is accepted and ignored.

For `ship merge` (U10): an open PR gets a pull-request `gate` run on its current head the first time
runs are listed for it (green, or red while a file fake-gh-gate-red exists); `pr merge <url> --merge`
merges the PR's head into its base on the remote with `git` (refused while fake-gh-gate-red exists).
`--match-head-commit SHA` refuses when the head moved; fake-gh-merge-noop says merged and merges nothing;
fake-gh-merge-moves-base (used once) pushes a commit to the base and refuses, as GitHub does when the
base moved. With a file fake-gh-auto, `workflow run` makes a finished run at once (green, or red while
fake-gh-deep-red exists) carrying the `deep-verdict` and `summary` artifacts for its head."""

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
    if argv[:2] == ["pr", "merge"]:
        found = next((p for p in prs if p["url"] == argv[2] or str(p["number"]) == argv[2]), None)
        if found is None or found["state"] != "OPEN":
            print(f"no open pull request {argv[2]}", file=sys.stderr)
            return 1
        if (home / "fake-gh-gate-red").exists():
            print("Pull request is not mergeable: the base branch policy prohibits the merge "
                  "(required status check gate is failing)", file=sys.stderr)
            return 1
        match = opt(argv, "--match-head-commit")
        if match and match != head_sha(found["head"]):
            print("Head branch was modified. Review and try the merge again.", file=sys.stderr)
            return 1
        if (home / "fake-gh-merge-moves-base").exists():
            (home / "fake-gh-merge-moves-base").unlink()
            move_base(found["baseRefName"])
            print("Base branch was modified. Review and try the merge again.", file=sys.stderr)
            return 1
        if (home / "fake-gh-merge-noop").exists():
            return 0  # says merged, merges nothing
        merge_on_remote(home, found)
        found["state"] = "MERGED"
        store.write_text(json.dumps(prs), "utf-8")
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
        sha = head_sha(branch)
        run = {"databaseId": new_id, "headSha": sha, "headBranch": branch,
               "event": "workflow_dispatch", "status": "queued", "conclusion": "",
               "displayTitle": f"{level} {branch}", "url": f"https://github.test/runs/{new_id}",
               "createdAt": "2026-11-13T00:00:00Z", "jobs": [], "artifacts": {}}
        if (home / "fake-gh-auto").exists():
            green = not (home / "fake-gh-deep-red").exists()
            summary = {"sha": sha, "ref": branch, "run_id": new_id, "url": run["url"], "level": level, "green": green,
                       "jobs": [], "reds": [], "quality": [], "mutants": {"killed": 0, "survived": 0, "new_survivors": 0},
                       "skipped": []}
            run.update({"status": "completed", "conclusion": "success" if green else "failure", "artifacts": {
                "deep-verdict": {"verdict.json": json.dumps({"sha": sha, "level": level})},
                "summary": {"summary.json": json.dumps(summary), "summary.md": "fake"}}})
        runs.insert(0, run)
        store.write_text(json.dumps(data), "utf-8")
        return 0
    if argv[:2] == ["run", "list"]:
        branch, event, commit = opt(argv, "--branch"), opt(argv, "--event"), opt(argv, "--commit")
        if event == "pull_request" and gate_runs(home, runs, branch):
            store.write_text(json.dumps(data), "utf-8")
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
                if (home / "fake-gh-gate-red").exists():
                    job.update({"status": "completed", "conclusion": "failure"})
        store.write_text(json.dumps(data), "utf-8")
        return 0
    print(f"fake gh: unsupported {argv}", file=sys.stderr)
    return 2


def gate_runs(home: Path, runs: list[dict], branch: str) -> bool:
    """A pull-request gate run for each open PR from `branch` at its current head, made once."""
    store = home / "fake-gh.json"
    prs = json.loads(store.read_text("utf-8")) if store.exists() else []
    made = False
    for p in prs:
        if p["head"] != branch or p["state"] != "OPEN":
            continue
        sha = head_sha(branch)
        if any(r["event"] == "pull_request" and r["headSha"] == sha and r["headBranch"] == branch for r in runs):
            continue
        new_id = max([r["databaseId"] for r in runs] + [1000]) + 1
        red = (home / "fake-gh-gate-red").exists()
        job = {"name": "gate", "databaseId": new_id * 10, "status": "completed",
               "conclusion": "failure" if red else "success", "url": f"https://github.test/runs/{new_id}/gate"}
        runs.insert(0, {"databaseId": new_id, "headSha": sha, "headBranch": branch, "event": "pull_request",
                        "status": "completed", "conclusion": job["conclusion"], "displayTitle": f"gate {branch}",
                        "url": f"https://github.test/runs/{new_id}", "createdAt": "2026-11-13T00:00:00Z",
                        "jobs": [job], "artifacts": {}})
        made = True
    return made


def merge_on_remote(home: Path, pr: dict) -> None:
    """`gh pr merge --merge`: a merge commit of the head into the base, pushed to the remote."""
    import tempfile

    git("fetch", "-q", "origin")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "merge"
        git("worktree", "add", "-q", "--detach", str(work), f"origin/{pr['baseRefName']}")
        try:
            subprocess.run(["git", "-c", "user.name=fake gh", "-c", "user.email=gh@test.invalid", "merge", "-q",
                            "--no-ff", "-m", f"Merge pull request #{pr['number']} from {pr['head']}",
                            f"origin/{pr['head']}"], cwd=work, check=True, capture_output=True, text=True)
            subprocess.run(["git", "push", "-q", "origin", f"HEAD:refs/heads/{pr['baseRefName']}"], cwd=work,
                           check=True, capture_output=True, text=True)
        finally:
            git("worktree", "remove", "--force", str(work))


def move_base(base: str) -> None:
    """Another program's merge lands on the base while this PR merges: one commit pushed there."""
    import tempfile

    git("fetch", "-q", "origin")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "other"
        git("worktree", "add", "-q", "--detach", str(work), f"origin/{base}")
        try:
            (work / "moved-by-another-merge.txt").write_text("x\n", "utf-8")
            for argv in (["add", "-A"],
                         ["-c", "user.name=other", "-c", "user.email=o@test.invalid", "commit", "-q", "-m",
                          "other program: merged"],
                         ["push", "-q", "origin", f"HEAD:refs/heads/{base}"]):
                subprocess.run(["git", *argv], cwd=work, check=True, capture_output=True, text=True)
        finally:
            git("worktree", "remove", "--force", str(work))


def head_sha(branch: str) -> str:
    out = git("ls-remote", "origin", f"refs/heads/{branch}")
    return out.split()[0] if out else ""


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
