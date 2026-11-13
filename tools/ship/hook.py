"""Claude Code PreToolUse hook: the guard every worker runs under (D-L9). It fails closed: any error
refuses (exit 2), and the role settings run it as `... hook ... || exit 2`.

File tools (Write, Edit, MultiEdit, NotebookEdit): allowed inside each held slice's worktree and its
current evidence folder, and the program's review/ and notes/ folders; refused everywhere else, the
main checkout included.

Bash commands are read segment by segment (split on `&&`, `||`, `;`, `|` and new lines), following
`cd`/`Set-Location`/`Push-Location`, and refused when they:
- run a git command that writes (commit, push, reset, checkout, switch, rebase, merge, a branch or tag
  change, clean, stash, add, rm, mv, restore, apply, am, cherry-pick, revert, pull, update-ref, worktree,
  a config write) anywhere but a held slice worktree, through `-C`, `cd`, `--git-dir` or `--work-tree`;
- force push, push with --mirror, --all, --tags, --delete or --prune, delete a remote branch, or push
  to any branch but the slice's own;
- name the main checkout, `~/.claude`, `cmdkey`, `keyring`, `CredRead` or the Windows credential store;
- run inline code or a nested shell (`python -c`, `python -`, `bash -c`, `sh -c`, `cmd /c`, `powershell`,
  `pwsh`), which the guard could not read.

The hook input does not say which agent is calling, so the allowed set is the union over held slices:
it stops writes to the main checkout and to anything outside the run, not one builder writing into
another held builder's worktree.

Roles (D-L16, FACTORY-DESIGN 11.3). The launcher puts `SHIP_ROLE` in every worker's environment, and the
hook process inherits it. `builder` and `fixer` (and no role at all, the hook's first callers) get the
held-slice rules above. Every other role writes only its own paths, named below from `SHIP_STOP`,
`SHIP_NOTES` and `SHIP_WORKTREE`, and runs no git that writes, except `docs` inside its docs worktree,
pushing only `SHIP_BRANCH`. A role the table does not know, or a role whose path variable is missing,
refuses every write.

| Role | Writes |
|---|---|
| reader, fault-reader | the one notes file `SHIP_NOTES` |
| verdict | `stop-review/<SHIP_STOP>/`, `merge/`, the sibling `<program>-fix-<SHIP_STOP>/` |
| grounding | `plan-review/grounding.md`, `grounding/REPORT.md` |
| plan-review | `plan-review/` |
| planner-fix, later-handoff, sweep-handoff | the plan files of the program folder |
| challenger, audit-judge, answer-linker | `CHALLENGE.md`, `AUDIT.md`, `CAN-CHANGE.md`, `decisions/proposed/` |
| audit-intent, audit-reader, audit-screen | `INTENT.md`, `readers/`, `AUDIT-SCREEN.md` (one each) |
| docs | its docs worktree `SHIP_WORKTREE` |

The main checkout comes from `state.json`, else `SHIP_REPO`. A non-builder role with neither gets every
Bash command refused: the guard cannot tell what names the main checkout.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

from ship import state as st
from ship.layout import Program
from ship.state import Status

FILE_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
SPLIT = re.compile(r"&&|\|\||;|\||\n")
CD_WORDS = {"cd", "set-location", "push-location", "pushd", "sl"}
GIT_WRITES = {"commit", "push", "reset", "checkout", "switch", "rebase", "merge", "tag", "clean", "stash", "add",
              "rm", "mv", "restore", "apply", "am", "cherry-pick", "revert", "pull", "update-ref", "worktree",
              "filter-branch", "gc", "prune", "replace", "notes"}
BRANCH_WRITE_FLAGS = {"-d", "-D", "--delete", "-m", "-M", "--move", "-c", "-C", "--copy", "-f", "--force",
                      "-u", "--unset-upstream", "--edit-description"}
PUSH_REFUSED = {"--mirror", "--all", "--tags", "--delete", "-d", "--prune"}
SECRET_WORDS = ("cmdkey", "keyring", "credread", "credwrite", "creddelete", "credenumerate", "vaultcmd",
                "credential manager", "credentialmanager", "storedcredential", "windows.security.credentials",
                "get-credential", "git-credential", "credential.helper")
SHELLS = {"bash", "sh", "zsh", "dash", "powershell", "pwsh", "cmd", "bash.exe", "sh.exe", "powershell.exe",
          "pwsh.exe", "cmd.exe"}
PYTHONS = {"python", "python3", "py", "python.exe", "python3.exe", "py.exe"}


def _norm(path: str) -> str:
    if sys.platform == "win32":
        drive = re.match(r"^/([a-zA-Z])(/|$)", path)  # Git Bash /d/x -> D:/x
        if drive:
            path = f"{drive.group(1)}:/{path[3:]}"
    return os.path.normcase(os.path.abspath(os.path.expanduser(path)))


def inside(path: str, root: str) -> bool:
    p, r = _norm(path), _norm(root)
    return p == r or p.startswith(r.rstrip(os.sep) + os.sep)


SLICE_ROLES = ("builder", "fixer", "")
PLAN_FILES = ("PROGRAM.yaml", "SCOPE.md", "GROUND.md", "CHALLENGE.md", "PLAN.md", "ANNEAL-LOG.md", "EDGE-CASES.md",
              "CAN-CHANGE.md", "REMOVED.md", "SLICES.md", "checks.toml", "WAITING.md", "decisions", "arch", "slices",
              "plan-review/FIXES.applied.md", "plan-review/FIXES.md")


def role_paths(program: Program, role: str, env) -> tuple[list[str], dict[str, str]]:
    """(writable roots, {worktree: the branch it may push}) for a role that is not a builder.
    Raises KeyError for a role the table does not know, ValueError for a missing path variable."""
    d = program.dir

    def need(name: str) -> str:
        value = (env.get(name) or "").strip()
        if not value:
            raise ValueError(f"role {role} needs {name} in its environment")
        return value

    if role in ("reader", "fault-reader"):
        return [need("SHIP_NOTES")], {}
    if role == "verdict":
        stop = need("SHIP_STOP")
        return [str(program.stop_review(stop)), str(d / "merge"), str(d.parent / f"{d.name}-fix-{stop}")], {}
    if role == "grounding":
        return [str(d / "plan-review" / "grounding.md"), str(d / "grounding" / "REPORT.md")], {}
    if role == "plan-review":
        return [str(d / "plan-review")], {}
    if role in ("planner-fix", "later-handoff", "sweep-handoff"):
        return [str(d / name) for name in PLAN_FILES], {}
    if role in ("challenger", "audit-judge", "answer-linker"):
        return [str(d / name) for name in ("CHALLENGE.md", "AUDIT.md", "CAN-CHANGE.md", "decisions/proposed")], {}
    if role == "audit-intent":
        return [str(d / "INTENT.md")], {}
    if role == "audit-reader":
        return [str(d / "readers")], {}
    if role == "audit-screen":
        return [str(d / "AUDIT-SCREEN.md")], {}
    if role == "docs":
        tree = need("SHIP_WORKTREE")
        return [tree], {tree: need("SHIP_BRANCH")}
    raise KeyError(f"role {role!r} is not in the hook's table")


class Run:
    """What the guard knows: held worktrees (with their branches), writable roots, the main checkout."""

    def __init__(self, program: Program, env=None):
        env = os.environ if env is None else env
        self.role = (env.get("SHIP_ROLE") or "").strip()
        if self.role in SLICE_ROLES:
            state = st.load(program)
            held = [s for s in state.slices.values() if s.status == Status.HELD]
            self.branches = {str(state.worktree(s.id)): s.branch for s in held}
            self.worktrees = list(self.branches)
            evidence = [str(program.evidence(s.id, s.attempts)) for s in held]
            self.roots = self.worktrees + evidence + [str(program.review_dir), str(program.notes_dir)]
            self.repo = state.repo
            return
        self.roots, self.branches = role_paths(program, self.role, env)
        self.worktrees = list(self.branches)
        self.repo = st.load(program).repo if program.state.exists() else ""
        self.repo = self.repo or (env.get("SHIP_REPO") or "").strip()

    def worktree_of(self, where: str) -> str | None:
        return next((w for w in self.worktrees if inside(where, w)), None)


def allowed_roots(program: Program) -> tuple[list[str], list[str]]:
    """(worktrees, every writable root)."""
    run = Run(program)
    return run.worktrees, run.roots


def _unquote(token: str) -> str:
    return token[1:-1] if len(token) >= 2 and token[0] == token[-1] and token[0] in "'\"" else token


def _tokens(segment: str) -> list[str]:
    try:
        return [_unquote(t) for t in shlex.split(segment, posix=False)]
    except ValueError:
        return segment.split()


def _name(token: str) -> str:
    return Path(token.replace("\\", "/")).name.lower()


def git_calls(command: str, cwd: str) -> list[tuple[str, str, list[str]]]:
    """(folder, subcommand, its arguments) for every git call in a shell command. A `--git-dir` or
    `--work-tree` makes the folder unknowable, reported as ""."""
    here, found = cwd, []
    for segment in SPLIT.split(command):
        tokens = _tokens(segment)
        if not tokens:
            continue
        if tokens[0].lower() in CD_WORDS and len(tokens) > 1:
            here = os.path.join(here, tokens[-1])
            continue
        names = [_name(t) for t in tokens]
        if "git" not in names and "git.exe" not in names:
            continue
        i = max(names.index(n) for n in ("git", "git.exe") if n in names) + 1
        where = here
        while i < len(tokens) and tokens[i].startswith("-"):
            flag = tokens[i]
            if flag in ("-C", "-c") and i + 1 < len(tokens):
                if flag == "-C":
                    where = os.path.join(where, tokens[i + 1])
                i += 2
                continue
            if flag.startswith(("--git-dir", "--work-tree")):
                where = ""
                i += 1 if "=" in flag else 2
                continue
            i += 1
        if i < len(tokens):
            found.append((where, tokens[i], tokens[i + 1:]))
    return found


def commit_dirs(command: str, cwd: str) -> list[str]:
    """The folder each `git commit` in a shell command runs in."""
    return [where for where, sub, _ in git_calls(command, cwd) if sub == "commit"]


def _writes(sub: str, args: list[str]) -> bool:
    if sub in GIT_WRITES:
        return True
    if sub == "branch":
        return any(a in BRANCH_WRITE_FLAGS or a.startswith("--set-upstream") for a in args) or \
            any(not a.startswith("-") for a in args)
    if sub == "config":
        return not any(a in ("--get", "--get-all", "--get-regexp", "--list", "-l") for a in args)
    return False


def _push_problem(args: list[str], branch: str | None) -> str | None:
    for flag in (a for a in args if a.startswith("-")):
        short_force = not flag.startswith("--") and "f" in flag[1:]
        if flag in PUSH_REFUSED or flag.startswith("--force") or short_force:
            return f"push {flag} is refused; push only your slice branch, never by force"
    positional = [a for a in args if not a.startswith("-")]
    for spec in positional[1:]:  # the first is the remote
        if spec.startswith("+"):
            return f"push {spec} is a force push; refused"
        src, colon, dst = spec.partition(":")
        if colon and not src:
            return f"push {spec} deletes a remote branch; refused"
        target = (dst if colon else src).removeprefix("refs/heads/")
        if target == "HEAD" and not colon:
            continue  # the current branch, which in a slice worktree is the slice's own
        if target != branch:
            return f"push to {target!r} refused; push only to your slice branch {branch!r}"
    return None


def _path_tokens(tokens: list[str]) -> list[str]:
    out = []
    for token in tokens:
        for part in (token, token.partition("=")[2]):
            if part and ("/" in part or "\\" in part or part.startswith("~")):
                out.append(part)
    return out


def bash_problem(run: Run, command: str, cwd: str) -> str | None:
    if not run.repo:
        return (f"ship hook: Bash refused: role {run.role} has no state.json and no SHIP_REPO, so the guard "
                "cannot tell what names the main checkout")
    low = command.lower().replace("\\", "/")
    for word in SECRET_WORDS:
        if word in low:
            return f"ship hook: Bash refused: it names {word!r}; workers never touch credentials"
    home = _norm(str(Path.home())).replace("\\", "/").lower()
    if any(x in low for x in ("~/.claude", "$home/.claude", "${home}/.claude", "%userprofile%/.claude",
                              "$env:userprofile/.claude", f"{home}/.claude")):
        return "ship hook: Bash refused: it names ~/.claude; workers never read or change his settings"
    here = cwd
    for segment in SPLIT.split(command):
        tokens = _tokens(segment)
        if not tokens:
            continue
        if tokens[0].lower() in CD_WORDS and len(tokens) > 1:
            here = os.path.join(here, tokens[-1])
        for path in _path_tokens(tokens):
            full = os.path.join(here, path)
            if inside(full, run.repo) and not any(inside(full, r) for r in run.roots):
                return f"ship hook: Bash refused: it names the main checkout ({path}); work only in your worktree"
        names = [_name(t) for t in tokens]
        for n, name in enumerate(names):
            nxt = [t.lower() for t in tokens[n + 1:n + 3]]
            if name in PYTHONS and nxt and (nxt[0] == "-" or nxt[0].startswith("-c")):
                return "ship hook: Bash refused: inline python code; put it in a test or a file in your worktree"
            if name in SHELLS and (name.startswith(("powershell", "pwsh"))
                                   or any(x in ("-c", "/c", "/k", "-command") for x in nxt)):
                return f"ship hook: Bash refused: a nested shell ({tokens[n]}) the guard cannot read"
    for where, sub, args in git_calls(command, cwd):
        if not _writes(sub, args):
            continue
        tree = run.worktree_of(where) if where else None
        if tree is None:
            shown = where or "a --git-dir or --work-tree folder"
            if run.role not in SLICE_ROLES:
                return f"ship hook: git {sub} in {shown} refused; role {run.role} runs no git that writes there"
            if sub == "commit":
                return f"ship hook: git commit in {shown} refused; commit only in your own slice worktree"
            return f"ship hook: git {sub} in {shown} refused; git writes only in your own slice worktree"
        if sub == "push":
            problem = _push_problem(args, run.branches[tree])
            if problem:
                return f"ship hook: git {problem}"
    return None


def decide(program: Program, event: dict) -> str | None:
    """None to allow, else the reason to refuse."""
    tool = event.get("tool_name", "")
    data = event.get("tool_input") or {}
    cwd = event.get("cwd") or os.getcwd()
    if tool not in FILE_TOOLS and tool != "Bash":
        return None
    try:
        run = Run(program)
    except Exception as exc:  # noqa: BLE001 - an unknown role or an unreadable state.json refuses
        return f"ship hook: cannot tell what this worker may write ({exc!r}); refusing writes until it can"
    if tool in FILE_TOOLS:
        target = os.path.join(cwd, data.get(FILE_TOOLS[tool], ""))
        if any(inside(target, r) for r in run.roots):
            return None
        if run.role in SLICE_ROLES:
            return f"ship hook: {tool} to {target} refused; write only in your worktree or evidence folder"
        return f"ship hook: {tool} to {target} refused; role {run.role} writes only {', '.join(run.roots)}"
    return bash_problem(run, str(data.get("command", "")), cwd)


def main(program: Program, raw: str) -> int:
    try:
        event = json.loads(raw or "{}")
        if not isinstance(event, dict):
            raise ValueError("hook input is not an object")
        reason = decide(program, event)
    except Exception as exc:  # noqa: BLE001 - the guard fails closed
        print(f"ship hook: refusing, the guard itself failed: {exc!r}", file=sys.stderr)
        return 2
    if reason:
        print(reason, file=sys.stderr)
        return 2
    return 0
