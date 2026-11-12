"""A stand-in for the `gh pr` calls the scripts make. PRs live in fake-gh.json in the git dir;
each PR's head sha is read from the real remote with `git ls-remote`."""

import json
import subprocess
import sys
from pathlib import Path


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def opt(args: list[str], name: str) -> str:
    return args[args.index(name) + 1]


def main(argv: list[str]) -> int:
    store = Path(git("rev-parse", "--git-common-dir")).resolve() / "fake-gh.json"
    prs = json.loads(store.read_text("utf-8")) if store.exists() else []
    if argv[:2] == ["pr", "create"]:
        url = f"https://github.test/pr/{len(prs) + 1}"
        prs.append({"url": url, "baseRefName": opt(argv, "--base"), "head": opt(argv, "--head"),
                    "title": opt(argv, "--title"), "body": Path(opt(argv, "--body-file")).read_text("utf-8"),
                    "state": "OPEN"})
        store.write_text(json.dumps(prs), "utf-8")
        print(url)
        return 0
    if argv[:2] == ["pr", "list"]:
        head = opt(argv, "--head")
        rows = [p for p in prs if p["head"] == head and p["state"] == "OPEN"]
        print(json.dumps([{**p, "headRefOid": head_sha(p["head"])} for p in rows]))
        return 0
    if argv[:2] == ["pr", "view"]:
        pr = next(p for p in prs if p["url"] == argv[2])
        print(json.dumps({**pr, "headRefOid": head_sha(pr["head"])}))
        return 0
    if argv[:2] == ["pr", "close"]:
        for p in prs:
            if p["url"] == argv[2]:
                p["state"] = "CLOSED"
        store.write_text(json.dumps(prs), "utf-8")
        return 0
    print(f"fake gh: unsupported {argv}", file=sys.stderr)
    return 2


def head_sha(branch: str) -> str:
    out = git("ls-remote", "origin", f"refs/heads/{branch}")
    return out.split()[0] if out else ""


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
