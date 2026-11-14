"""Claude Code PreToolUse hook: the guard every worker runs under (D-L9, D-L22). It fails closed: any error
refuses (exit 2), and the role settings run it as `... hook ... || exit 2`.

Every worker has `SHIP_ROLE` (the launcher sets it); a missing or unknown role refuses everything, and
`SHIP_STOP` and `SHIP_PART`, when set, must be plain names (`[A-Za-z0-9_-]+`).

File tools (Write, Edit, MultiEdit, NotebookEdit) write only the role's paths (the table below). No role
writes `<program>/.kit/` (the kit's own files: `review-run.json`, `MERGE-BASE`, `gates.log`) or `<program>/.desk/`
(his answers, written by the front desk: D-L25), no role writes `notes/stop-*.json` (only the build loop does),
and a docs worktree is never the main checkout. No role writes a worktree's `ci/baselines/` or `contracts/`
(D-L25: they change only through the kit's generators at merge, so a commit touching only them is the kit's),
by file tool, redirection or a git command naming them. No role but a builder writes a `*.py` file,
`conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg` or `tox.ini` (D-L25: no worker runs code of its own).

Bash is an allow-list (D-L22). A command is read segment by segment (split on `&&`, `||`, `;`, `|`, `&`
and new lines, outside quotes), following `cd`/`Set-Location`/`Push-Location`. Each segment runs one of:
- `git` (its writes are judged below; no `-c` overrides and none of the subcommands that run other
  programs: bisect, submodule, difftool, mergetool);
- `uv run [flags]` followed by an allowed tool (no `--with`, `--script` or unknown flags; never `uvx` or
  another `uv` command);
- the kit's `timed` wrapper (`python -m ship timed ... -- <argv>`, `python <kit> timed ... -- <argv>`)
  followed by an allowed tool or `uv run`, or the kit's read-only `phase`;
- an allowed tool: `pytest`, `python -m pytest`, `ruff`, `pyright`, `mypy`, and a factory script
  `python <factory_home>/skills/<skill>/scripts/<name>.py` from the role's own list (`ROLE_SCRIPTS`, D-L25:
  grounding his_words, check_chain, check_plan; plan-review check_chain, check_plan; verdict check_plan; the
  planning and audit roles the scripts their prompts name). A factory script's output path (`--out`,
  `--output`, `-o`, and the program folder of `chain_packet.py` and `sweep_briefs.py`) must be one the role
  writes; `--ship` (and `check_plan.py`'s second argument) must be this kit, since those scripts import it;
  `check_chain.py --rerun-facts` is refused (it runs commands a planner wrote); `probe_tests.py --python` takes
  only an interpreter inside its `--checkout` or the one running the kit.
A role other than a builder runs pytest only on code it did not write: no path argument inside the program
folder, and none of `-p` (but `-p no:<plugin>`), `-c`, `--config-file`, `-o`, `--override-ini`, `--rootdir`,
`--confcutdir`, `--doctest-glob`.
Python is any name `python`, `python3.12`, `pythonw`, `py` (with `.exe`); a flag cluster holding `c`
(`-c`, `-Ic`) or a lone `-` is inline code and refused. Anything else (`gh`, `node`, `cp`, `env`, a nested
shell, a leading `VAR=value`, `$(...)` or backticks) is refused. Redirection (`>`, `>>`, `tee`) is refused
for every role but a builder, which may redirect only into its worktree (a `2>&1` duplicate and the null
device are allowed).

Paths a command names are checked too: never the main checkout, `~/.claude` or `.kit/`; and inside the
program folder (or its sibling fix folders) only the program folder itself and the role's own paths (a
reader's `stop-review/<X>/runs/` included), except the arguments of a factory script. `git --output` is
refused. Git writes (commit, push, reset, checkout, switch, rebase, merge, a branch or tag change,
clean, stash, add, rm, mv, restore, apply, am, cherry-pick, revert, pull, update-ref, worktree, a config
write) happen only in a held slice worktree (builders) or the docs worktree (docs), never through
`--git-dir` or `--work-tree`; no force push, no `--mirror`, `--all`, `--tags`, `--delete` or `--prune`, no
remote branch deletion, and a push only to the worker's own branch. A command naming `cmdkey`, `keyring`,
`CredRead` or the credential store is refused.

The hook input does not say which agent is calling, so a builder's allowed set is the union over held
slices: it stops writes to the main checkout and outside the run, not one builder writing into another
held builder's worktree.

| Role | Writes |
|---|---|
| builder, fixer | each held slice's worktree and current evidence folder, `review/`, `notes/` but `notes/stop-*.json` |
| reader, fault-reader | the one notes file `SHIP_NOTES` (and run logs in `stop-review/<SHIP_STOP>/runs/`) |
| verdict | `stop-review/<SHIP_STOP>/REVIEW*.md` and `WAITS.md`, `merge/<SHIP_STOP>-pr.md`, the plan files of the sibling `<program>-fix-<SHIP_STOP>/` (never its `ship.toml` or `checks.toml`: the kit copies those) |
| grounding | `plan-review/grounding.md`, `grounding/REPORT.md` |
| plan-review | `plan-review/` |
| planner-fix, later-handoff | the plan files of the program folder |
| sweep-handoff | `SLICES.md`, `slices/`, `PROGRAM.yaml`, `EDGE-CASES.md`, `arch/`, `AUDIT.md`, `notes/` |
| challenger, answer-linker | `CHALLENGE.md`, `CAN-CHANGE.md`, `decisions/proposed/`, `challenge/`, `subtract/` |
| audit-judge | `FINDINGS.tsv`, `AUDIT.md`, `CHALLENGE.md`, `CAN-CHANGE.md`, `REMOVED.md`, `decisions/proposed/`, `challenge/`, `subtract/` |
| audit-intent | `INTENT.md` |
| audit-reader | its part only (`SHIP_PART`): `readers/<part>.md`, `readers/<part>.tsv`, `readers/<part>-runs/`, `runs/`, `heartbeat/audit-<part>` |
| audit-screen | `AUDIT-SCREEN.md` (D-L18) |
| docs | its docs worktree `SHIP_WORKTREE` |

The main checkout comes from `state.json`, else `SHIP_REPO`. A role with neither gets every Bash command
refused: the guard cannot tell what names the main checkout.
"""

from __future__ import annotations

import fnmatch
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
CD_WORDS = {"cd", "set-location", "push-location", "pushd", "sl"}
GIT_WRITES = {"commit", "push", "reset", "checkout", "switch", "rebase", "merge", "tag", "clean", "stash", "add",
              "rm", "mv", "restore", "apply", "am", "cherry-pick", "revert", "pull", "update-ref", "worktree",
              "filter-branch", "gc", "prune", "replace", "notes"}
GIT_RUNS_PROGRAMS = {"bisect", "submodule", "difftool", "mergetool", "daemon", "instaweb", "filter-branch",
                     "credential", "credential-store", "credential-cache"}
BRANCH_WRITE_FLAGS = {"-d", "-D", "--delete", "-m", "-M", "--move", "-c", "-C", "--copy", "-f", "--force",
                      "-u", "--unset-upstream", "--edit-description"}
PUSH_REFUSED = {"--mirror", "--all", "--tags", "--delete", "-d", "--prune"}
SECRET_WORDS = ("cmdkey", "keyring", "credread", "credwrite", "creddelete", "credenumerate", "vaultcmd",
                "credential manager", "credentialmanager", "storedcredential", "windows.security.credentials",
                "get-credential", "git-credential", "credential.helper")
PYTHON = re.compile(r"(python|pythonw|py)(\d+(\.\d+)*)?w?(\.exe)?")
TOOLS = {"pytest", "py.test", "ruff", "pyright", "mypy"}
TOOL_MODULES = {"pytest", "ruff", "pyright", "mypy"}
PYTHON_FLAGS = set("IBuEsSOqbdvxRP")  # single-letter interpreter flags that run no code of their own
UV_FLAGS = {"--no-sync", "--frozen", "--locked", "--offline", "-q", "--quiet", "--no-dev", "--all-extras",
            "--all-packages", "--exact", "--no-editable"}
UV_VALUED = {"--directory", "--project", "--package", "--extra", "--group", "--only-group", "--no-group"}
NULL_SINKS = {"/dev/null", "nul", "$null"}
TEE = {"tee", "tee.exe", "tee-object"}
PLAIN = re.compile(r"[A-Za-z0-9_-]+")
PLAIN_SLICE = re.compile(r"[A-Za-z0-9_.-]+")


def _norm(path: str) -> str:
    if sys.platform == "win32":
        drive = re.match(r"^/([a-zA-Z])(/|$)", path)  # Git Bash /d/x -> D:/x
        if drive:
            path = f"{drive.group(1)}:/{path[3:]}"
    return os.path.normcase(os.path.abspath(os.path.expanduser(path)))


def inside(path: str, root: str) -> bool:
    p, r = _norm(path), _norm(root)
    return p == r or p.startswith(r.rstrip(os.sep) + os.sep)


def in_root(path: str, root: str) -> bool:
    """`root` is a file or folder, or a file glob (`.../REVIEW*.md`) whose last part holds a `*`."""
    name = Path(root).name
    if "*" in name:
        return _norm(str(Path(path).parent)) == _norm(str(Path(root).parent)) and \
            fnmatch.fnmatch(os.path.normcase(Path(path).name), os.path.normcase(name))
    return inside(path, root)


SLICE_ROLES = ("builder", "fixer")
PLAN_FILES = ("PROGRAM.yaml", "SCOPE.md", "GROUND.md", "CHALLENGE.md", "PLAN.md", "ANNEAL-LOG.md", "EDGE-CASES.md",
              "CAN-CHANGE.md", "REMOVED.md", "SLICES.md", "checks.toml", "WAITING.md", "decisions", "arch", "slices",
              "plan-review/FIXES.applied.md", "plan-review/FIXES.md")
FIX_FILES = tuple(f for f in PLAN_FILES if f != "checks.toml")  # D-L22: the kit copies a fix folder's settings
HIS_WORDS = "factory-core/scripts/his_words.py"
CHECK_CHAIN = "factory-core/scripts/check_chain.py"
CHECK_PLAN = "factory-core/scripts/check_plan.py"
CHAIN_PACKET = "factory-core/scripts/chain_packet.py"
CALLERS = "audit-area/scripts/callers.py"
LINT_FINDINGS = "audit-area/scripts/lint_findings.py"
SWEEP_BRIEFS = "audit-area/scripts/sweep_briefs.py"
# D-L25: the factory scripts (`<skill>/scripts/<name>.py` under `<factory_home>/skills`) each role may run, and
# no other. The planning and audit roles get the scripts their prompts name; probe, census, collect and
# apply_screen are the conveyor's own children, never a worker's.
ROLE_SCRIPTS = {
    "grounding": (HIS_WORDS, CHECK_CHAIN, CHECK_PLAN),
    "plan-review": (CHECK_CHAIN, CHECK_PLAN),
    "verdict": (CHECK_PLAN,),
    "planner-fix": (CHAIN_PACKET, CHECK_CHAIN, CHECK_PLAN),
    "later-handoff": (CHAIN_PACKET, CHECK_CHAIN, CHECK_PLAN),
    "sweep-handoff": (CHAIN_PACKET, CHECK_CHAIN, CHECK_PLAN, SWEEP_BRIEFS),
    "challenger": (CHECK_CHAIN,),
    "answer-linker": (CHECK_CHAIN,),
    "audit-intent": (HIS_WORDS, CHECK_CHAIN),
    "audit-judge": (CALLERS, CHECK_CHAIN, LINT_FINDINGS),
    "audit-reader": (CALLERS, LINT_FINDINGS),
    "audit-screen": (),
}
SCRIPT_ROLES = tuple(ROLE_SCRIPTS)
OTHER_ROLES = ("reader", "fault-reader", "docs") + SCRIPT_ROLES
GENERATOR_DIRS = ("ci/baselines", "contracts")  # D-L25: written only by the kit's generators at merge
CODE_NAMES = ("conftest.py", "pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini")  # with `*.py`: builders only
OUT_FLAGS = ("--out", "--output", "-o")
PYTEST_REFUSED = ("-c", "--config-file", "-o", "--override-ini", "--rootdir", "--confcutdir", "--doctest-glob")
PYTEST_VALUED = ("-p", "-k", "-m", "-n", "-W", "--junitxml", "--junit-xml", "--timeout", "--basetemp", "--dist",
                 "--maxfail", "--tb", "--deselect", "--ignore", "--ignore-glob", "--log-file", "--durations", "-r")


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
        stop = (env.get("SHIP_STOP") or "").strip()
        return [need("SHIP_NOTES")] + ([str(program.stop_review(stop) / "runs")] if stop else []), {}
    if role == "verdict":
        stop = need("SHIP_STOP")
        fix = d.parent / f"{d.name}-fix-{stop}"
        return [str(program.stop_review(stop) / "REVIEW*.md"), str(program.stop_review(stop) / "WAITS.md"),
                str(d / "merge" / f"{stop}-pr.md")] + [str(fix / name) for name in FIX_FILES], {}
    if role == "grounding":
        return [str(d / "plan-review" / "grounding.md"), str(d / "grounding" / "REPORT.md")], {}
    if role == "plan-review":
        return [str(d / "plan-review")], {}
    if role in ("planner-fix", "later-handoff"):
        return [str(d / name) for name in PLAN_FILES], {}
    if role == "sweep-handoff":
        return [str(d / name) for name in ("SLICES.md", "slices", "PROGRAM.yaml", "EDGE-CASES.md", "arch", "AUDIT.md",
                                           "notes")], {}
    if role in ("challenger", "answer-linker"):
        return [str(d / name) for name in ("CHALLENGE.md", "CAN-CHANGE.md", "decisions/proposed", "challenge",
                                           "subtract")], {}
    if role == "audit-judge":
        return [str(d / name) for name in ("FINDINGS.tsv", "AUDIT.md", "CHALLENGE.md", "CAN-CHANGE.md", "REMOVED.md",
                                           "decisions/proposed", "challenge", "subtract")], {}
    if role == "audit-intent":
        return [str(d / "INTENT.md")], {}
    if role == "audit-reader":
        part = need("SHIP_PART")
        return [str(d / "readers" / f"{part}.md"), str(d / "readers" / f"{part}.tsv"),
                str(d / "readers" / f"{part}-runs"), str(d / "runs"), str(d / "heartbeat" / f"audit-{part}")], {}
    if role == "audit-screen":
        return [str(d / "AUDIT-SCREEN.md")], {}
    if role == "docs":
        tree = need("SHIP_WORKTREE")
        return [tree], {tree: need("SHIP_BRANCH")}
    raise KeyError(f"role {role!r} is not in the hook's table")


def kit_dir() -> str:
    return str(Path(__file__).resolve().parent)


class Run:
    """What the guard knows: the role, held worktrees (with their branches), writable roots, the main
    checkout, the factory home."""

    def __init__(self, program: Program, env=None):
        env = os.environ if env is None else env
        self.program = program
        self.role = (env.get("SHIP_ROLE") or "").strip()
        if not self.role:
            raise ValueError("no SHIP_ROLE: the guard cannot tell what this worker may do")
        if self.role not in SLICE_ROLES + OTHER_ROLES:
            raise KeyError(f"role {self.role!r} is not in the hook's table")
        for name in ("SHIP_STOP", "SHIP_PART"):
            value = (env.get(name) or "").strip()
            if value and not PLAIN.fullmatch(value):
                raise ValueError(f"{name} {value!r} is not a plain name ([A-Za-z0-9_-]+)")
        from ship.launch import factory_home
        from ship.settings import load_settings

        self.factory = str(factory_home(load_settings(program.dir)))
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
        if self.role == "docs" and self.repo and any(inside(w, self.repo) for w in self.worktrees):
            raise ValueError("the docs worktree is the main checkout")

    def worktree_of(self, where: str) -> str | None:
        return next((w for w in self.worktrees if inside(where, w)), None)

    def may_write(self, target: str) -> bool:
        return any(in_root(target, r) for r in self.roots)

    def fix_folders(self) -> list[Path]:
        d = self.program.dir
        return [p for p in d.parent.glob(f"{d.name}-fix-*") if p.is_dir()] if d.parent.is_dir() else []

    def kit_owned(self, target: str) -> bool:
        """`.kit/` of the program or of a fix folder: the kit's own files (D-L22); and `.desk/`, his answers as
        the front desk wrote them (D-L25)."""
        return any(inside(target, str(Path(folder) / name))
                   for folder in [self.program.dir, *self.fix_folders()] for name in (".kit", ".desk"))

    def generated(self, target: str) -> bool:
        """A worktree's `ci/baselines/` or `contracts/` (D-L25), whatever the role."""
        for tree in self.worktrees:
            if inside(target, tree):
                rel = os.path.relpath(_norm(target), _norm(tree)).replace("\\", "/")
                return any(rel == d or rel.startswith(d + "/") for d in GENERATOR_DIRS)
        return False

    def code_refused(self, target: str) -> bool:
        """D-L25: no role but a builder writes Python or a test or packaging config."""
        name = Path(target).name.lower()
        return self.role not in SLICE_ROLES and (name.endswith((".py", ".pyw", ".pyi")) or name in CODE_NAMES)

    def builder_refused(self, target: str) -> bool:
        """D-L22: a builder never writes a stop note (it would say the stop is built); nor does any other
        role whose paths hold `notes/` (sweep-handoff)."""
        return any(_norm(str(Path(target).parent)) == _norm(str(folder / "notes"))
                   and fnmatch.fnmatch(Path(target).name.lower(), "stop-*.json")
                   for folder in [self.program.dir, *self.fix_folders()])


def allowed_roots(program: Program) -> tuple[list[str], list[str]]:
    """(worktrees, every writable root)."""
    run = Run(program)
    return run.worktrees, run.roots


# ---- reading a shell command ----------------------------------------------------------------------


def _unquote(token: str) -> str:
    return token[1:-1] if len(token) >= 2 and token[0] == token[-1] and token[0] in "'\"" else token


def _tokens(segment: str) -> list[str]:
    try:
        return [_unquote(t) for t in shlex.split(segment, posix=False)]
    except ValueError:
        return segment.split()


def _name(token: str) -> str:
    return Path(token.replace("\\", "/")).name.lower()


def segments(command: str) -> list[str]:
    """Split on `&&`, `||`, `;`, `|`, `&` and new lines outside quotes. A `&` that is part of a
    redirection (`2>&1`, `&>`) does not split."""
    out, buf, quote, i = [], [], "", 0
    while i < len(command):
        ch = command[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            buf.append(ch)
            i += 1
            continue
        two = command[i:i + 2]
        if two in ("&&", "||"):
            out.append("".join(buf))
            buf = []
            i += 2
            continue
        if ch == "&" and (two == "&>" or (buf and buf[-1] == ">")):
            buf.append(ch)
            i += 1
            continue
        if ch in ";|&\n":
            out.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    out.append("".join(buf))
    return [x for x in out if x.strip()]


def redirections(segment: str) -> tuple[str, list[str]]:
    """(the segment without its output redirections, their targets). A duplicate (`2>&1`) has the target
    `&1`; input redirection is left alone."""
    text: list[str] = []
    targets: list[str] = []
    quote, i = "", 0
    while i < len(segment):
        ch = segment[i]
        if quote:
            text.append(ch)
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            text.append(ch)
            i += 1
            continue
        if ch != ">":
            text.append(ch)
            i += 1
            continue
        while text and (text[-1].isdigit() or text[-1] == "&"):  # 2>, &>
            text.pop()
        i += 1
        while i < len(segment) and segment[i] in ">|":
            i += 1
        while i < len(segment) and segment[i] == " ":
            i += 1
        start = i
        if i < len(segment) and segment[i] in "'\"":
            end = segment.find(segment[i], i + 1)
            end = len(segment) if end < 0 else end + 1
        else:
            end = i
            while end < len(segment) and not segment[end].isspace():
                end += 1
        targets.append(_unquote(segment[start:end]))
        text.append(" ")
        i = end
    return "".join(text), targets


def git_calls(command: str, cwd: str) -> list[tuple[str, str, list[str]]]:
    """(folder, subcommand, its arguments) for every git call in a shell command. A `--git-dir` or
    `--work-tree` makes the folder unknowable, reported as ""."""
    here, found = cwd, []
    for segment in segments(command):
        tokens = _tokens(redirections(segment)[0])
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


def _path_tokens(tokens: list[str], here: str) -> list[str]:
    """Tokens (or a flag's `=value`) that look like paths: a slash, a leading `~` or `.`, or a name that
    exists where the command runs."""
    out = []
    for token in tokens:
        part = token.partition("=")[2] if token.startswith("-") else token
        if not part:
            continue
        if "/" in part or "\\" in part or part.startswith(("~", ".")) or os.path.exists(os.path.join(here, part)):
            out.append(part)
    return out


# ---- the allow-list ---------------------------------------------------------------------------------


def factory_script(run: Run, script: str, here: str) -> str | None:
    """`<skill>/scripts/<name>.py` when `script` is `<factory_home>/skills/<skill>/scripts/<name>.py` and on the
    role's own list (`ROLE_SCRIPTS`, D-L25); else None."""
    if run.role not in ROLE_SCRIPTS or not run.factory:
        return None
    full = os.path.join(here, script)
    skills = os.path.join(run.factory, "skills")
    if not inside(full, skills):
        return None
    parts = os.path.relpath(_norm(full), _norm(skills)).replace("\\", "/").split("/")
    if not (len(parts) == 3 and parts[1] == "scripts" and parts[2].endswith(".py") and ".." not in parts):
        return None
    rel = "/".join(parts)
    allowed = {os.path.normcase(x): x for x in ROLE_SCRIPTS[run.role]}
    return allowed.get(os.path.normcase(rel))


def _flag_values(args: list[str], flags: tuple[str, ...]) -> list[str]:
    """The values of `flags` (`--out x` or `--out=x`) among a command's arguments."""
    out = []
    for i, a in enumerate(args):
        key, eq, value = a.partition("=")
        if key in flags:
            if eq:
                out.append(value)
            elif i + 1 < len(args):
                out.append(args[i + 1])
    return out


def _positionals(args: list[str], valued: tuple[str, ...]) -> list[str]:
    out, skip = [], False
    for a in args:
        if skip:
            skip = False
            continue
        if a.startswith("-"):
            skip = "=" not in a and a in valued
            continue
        out.append(a)
    return out


SCRIPT_VALUED = ("--out", "--output", "-o", "--ship", "--python", "--checkout", "--src", "--project", "--stage",
                 "--kind", "--transcripts", "--rerun-facts", "--repo", "--tip", "--registries", "--exclude",
                 "--ui-ref", "--challenge", "--prefix", "--dir", "--since", "--import-name", "--timeout")


def script_args_problem(run: Run, script: str, args: list[str], here: str) -> str | None:
    """D-L25: what a factory script writes, imports or runs must stay the role's own."""
    def full(path: str) -> str:
        return os.path.join(here, path)

    for value in _flag_values(args, OUT_FLAGS):
        if run.kit_owned(full(value)) or not run.may_write(full(value)):
            return f"{script} writes {value}, which role {run.role} does not write"
    name = script.rsplit("/", 1)[-1]
    positional = _positionals(args, SCRIPT_VALUED)
    ships = _flag_values(args, ("--ship",)) + (positional[1:2] if name == "check_plan.py" else [])
    for value in ships:
        if _norm(full(value)) != _norm(kit_dir()):
            return f"{script} imports the kit from {value}; only this kit ({kit_dir()})"
    if name == "check_chain.py" and _flag_values(args, ("--rerun-facts",)) + [a for a in args if a == "--rerun-facts"]:
        return "check_chain.py --rerun-facts runs the briefs' commands; a worker never does"
    writes = {"chain_packet.py": "slices", "sweep_briefs.py": "SLICES.md"}.get(name)
    if writes:
        if not positional:
            return f"{script} with no program folder"
        target = os.path.join(full(positional[0]), writes)
        if not run.may_write(target):
            return f"{script} writes {target}, which role {run.role} does not write"
    if name == "probe_tests.py":
        checkouts = _flag_values(args, ("--checkout",))
        for value in _flag_values(args, ("--python",)):
            own = _norm(full(value)) == _norm(sys.executable)
            in_checkout = any(inside(full(value), full(c)) for c in checkouts)
            if not (own or in_checkout):
                return f"probe_tests.py --python {value}: only the checkout's interpreter or the kit's"
    return None


def pytest_problem(run: Run, args: list[str], here: str) -> str | None:
    """D-L25: a role other than a builder never runs code of its own through pytest."""
    if run.role in SLICE_ROLES:
        return None
    for i, a in enumerate(args):
        key = a.split("=", 1)[0]
        if key in PYTEST_REFUSED or (key.startswith("-p") and key not in ("-p",) and not a.startswith("-pno:")):
            return f"pytest {key}: role {run.role} runs only the repo's own tests and config"
        if key == "-p":
            value = args[i + 1] if i + 1 < len(args) else ""
            if not value.startswith("no:"):
                return f"pytest -p {value}: role {run.role} loads no plugin"
    folders = [str(run.program.dir)] + [str(f) for f in run.fix_folders()]
    positional = _positionals(args, PYTEST_VALUED)
    if not positional and any(inside(here, f) for f in folders):
        return f"pytest with no path in {here}: role {run.role} never runs code from the program folder"
    for a in positional:
        target = os.path.join(here, a.split("::", 1)[0])
        if any(inside(target, f) for f in folders):
            return f"pytest {a}: role {run.role} never runs code from the program folder"
    return None


def kit_script(script: str, here: str) -> bool:
    full = _norm(os.path.join(here, script))
    return full in (_norm(kit_dir()), _norm(os.path.join(kit_dir(), "__main__.py")))


def kit_problem(run: Run, args: list[str], here: str, depth: int) -> str | None:
    """The kit itself: `timed ... -- <argv>` (the argv judged again) or the read-only `phase`."""
    sub = args[0] if args else ""
    if sub == "phase" and not any(a.startswith("--set") for a in args):
        return None
    if sub != "timed":
        return f"ship {sub or '(nothing)'}; a worker runs only ship timed and ship phase"
    if "--slice" in args:
        at = args.index("--slice") + 1
        name = args[at] if at < len(args) else ""
        if not PLAIN_SLICE.fullmatch(name) or ".." in name:
            return f"ship timed --slice {name!r} is not a plain name"
    if "--" not in args:
        return "ship timed with no `--` before its command"
    rest = args[args.index("--") + 1:]
    if not rest:
        return "ship timed with no command"
    return command_problem(run, rest, here, depth + 1)


def python_problem(run: Run, tokens: list[str], here: str, depth: int) -> str | None:
    """tokens[0] is a python. Allowed: `-m pytest|ruff|pyright|mypy`, the kit, a factory script."""
    rest, i, module = tokens[1:], 0, None
    launcher = _name(tokens[0]).startswith("py") and not _name(tokens[0]).startswith("python")
    while i < len(rest) and rest[i].startswith("-") and rest[i] != "-":
        flag = rest[i]
        if launcher and re.fullmatch(r"-\d+(\.\d+)?(-\d+)?", flag):
            i += 1
            continue
        if flag in ("-X", "-W"):
            i += 2
            continue
        if flag.startswith("--"):
            return f"python {flag}"
        body = flag[1:]
        if "c" in body:
            return "inline python code"
        if "m" in body:
            before, after = body.split("m", 1)
            if not set(before) <= PYTHON_FLAGS:
                return f"python {flag}"
            module = after or (rest[i + 1] if i + 1 < len(rest) else "")
            i += 1 if after else 2
            break
        if not set(body) <= PYTHON_FLAGS:
            return f"python {flag}"
        i += 1
    if module is not None:
        if module == "pytest":
            return pytest_problem(run, rest[i:], here)
        if module in TOOL_MODULES:
            return None
        if module == "ship":
            return kit_problem(run, rest[i:], here, depth)
        return f"python -m {module}"
    if i >= len(rest):
        return "a bare python"
    if rest[i] == "-":
        return "inline python code"
    script = rest[i]
    if kit_script(script, here):
        return kit_problem(run, rest[i + 1:], here, depth)
    named = factory_script(run, script, here)
    if named:
        return script_args_problem(run, named, rest[i + 1:], here)
    return f"python {script}"


def uv_problem(run: Run, args: list[str], here: str, depth: int) -> str | None:
    if not args or args[0] != "run":
        return f"uv {args[0] if args else ''}; only `uv run` with a test, lint or type tool"
    i = 1
    while i < len(args):
        a = args[i]
        if a == "--":
            i += 1
            break
        if not a.startswith("-"):
            break
        key = a.split("=", 1)[0]
        if key in UV_VALUED:
            i += 1 if "=" in a else 2
            continue
        if key in UV_FLAGS:
            i += 1
            continue
        return f"uv run {key}"  # --with, --with-editable, --script, --python and anything unknown
    rest = args[i:]
    if not rest:
        return "uv run with no command"
    return command_problem(run, rest, here, depth + 1)


def command_problem(run: Run, tokens: list[str], here: str, depth: int = 0) -> str | None:
    """None when a segment's command is on the allow-list. `depth` > 0 is after `uv run` or `timed`, where
    only the tools, the kit and `uv run` may follow."""
    if depth > 4:
        return "commands nested too deep"
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
        return f"an environment assignment ({tokens[0].split('=', 1)[0]}=)"
    name = _name(tokens[0])
    if name in ("git", "git.exe"):
        return None if depth == 0 else "git after uv run or ship timed"
    if name in ("uv", "uv.exe"):
        return uv_problem(run, tokens[1:], here, depth)
    if PYTHON.fullmatch(name):
        return python_problem(run, tokens, here, depth)
    if name.removesuffix(".exe") in TOOLS:
        return pytest_problem(run, tokens[1:], here) if name.removesuffix(".exe") in ("pytest", "py.test") else None
    if name in TEE:
        return None if depth == 0 else "tee after uv run or ship timed"  # its files are judged as redirections
    return f"{tokens[0]} is not on the guard's list (git, uv run, ship timed, pytest, ruff, pyright, mypy)"


def git_problem(tokens: list[str]) -> str | None:
    """Git that runs other programs or writes a file a guard cannot see."""
    names = [_name(t) for t in tokens]
    i = names.index("git") if "git" in names else names.index("git.exe")
    rest = tokens[i + 1:]
    j = 0
    while j < len(rest) and rest[j].startswith("-"):
        flag = rest[j]
        if flag == "-c" or flag.startswith(("--config-env", "--exec-path")):
            return f"git {flag} overrides git's config or programs"
        j += 2 if flag == "-C" else 1
    sub = rest[j] if j < len(rest) else ""
    if sub in GIT_RUNS_PROGRAMS:
        return f"git {sub} runs other programs"
    if any(t.startswith(("--output", "-O", "--open-files-in-pager", "--ext-diff", "--exec", "-x"))
           and sub in ("log", "diff", "show", "grep", "format-patch", "rebase") for t in rest[j + 1:]):
        return f"git {sub} with an option that writes a file or runs a program"
    return None


# ---- the decision -----------------------------------------------------------------------------------


def path_problem(run: Run, path: str, here: str, script_args: bool) -> str | None:
    full = os.path.join(here, path)
    if run.kit_owned(full):
        return f"it names {path}, the kit's own folder (.kit/) or the desk's (.desk/)"
    if run.repo and inside(full, run.repo) and not run.may_write(full):
        return f"it names the main checkout ({path}); work only in your worktree"
    folders = [str(run.program.dir)] + [str(f) for f in run.fix_folders()]
    if script_args or not any(inside(full, f) for f in folders):
        return None
    if _norm(full) == _norm(str(run.program.dir)) or run.may_write(full):
        return None
    return f"it names {path} in the program folder, which role {run.role} does not write"


def redirect_problem(run: Run, target: str, here: str) -> str | None:
    if target.startswith("&") or target.lower() in NULL_SINKS:
        return None
    full = os.path.join(here, target)
    if run.role not in SLICE_ROLES:
        return f"redirection to {target}; role {run.role} writes files only with its file tools"
    if run.worktree_of(full) is None or run.kit_owned(full):
        return f"redirection to {target}; a builder redirects only into its worktree"
    if run.generated(full):
        return f"redirection to {target}; ci/baselines/ and contracts/ change only through the kit's generators"
    return None


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
    if "$(" in command or "`" in command or "<(" in command or ">(" in command:
        return "ship hook: Bash refused: a command substitution the guard cannot read"
    here = cwd
    for segment in segments(command):
        text, targets = redirections(segment)
        tokens = _tokens(text)
        if not tokens:
            continue
        for target in targets:
            bad = redirect_problem(run, target, here)
            if bad:
                return f"ship hook: Bash refused: {bad}"
        if tokens[0].lower() in CD_WORDS:
            if len(tokens) > 1:
                bad = path_problem(run, tokens[-1], here, False)
                if bad:
                    return f"ship hook: Bash refused: {bad}"
                here = os.path.join(here, tokens[-1])
            continue
        bad = command_problem(run, tokens, here)
        if bad:
            scripts = ", ".join(x.rsplit("/", 1)[-1] for x in ROLE_SCRIPTS.get(run.role, ()))
            return (f"ship hook: Bash refused: {bad}; role {run.role} runs only git, uv run, ship timed, pytest, "
                    "ruff, pyright and mypy" + (f" and the factory scripts {scripts}" if scripts else ""))
        name = _name(tokens[0])
        if name in TEE:
            for target in [t for t in tokens[1:] if not t.startswith("-")]:
                bad = redirect_problem(run, target, here)
                if bad:
                    return f"ship hook: Bash refused: {bad}"
        is_git = name in ("git", "git.exe")
        if is_git:
            bad = git_problem(tokens)
            if bad:
                return f"ship hook: Bash refused: {bad}"
        script = PYTHON.fullmatch(name) is not None and any(factory_script(run, t, here) for t in tokens[1:3])
        writes = is_git and _git_writes_tokens(tokens)
        for path in _path_tokens(tokens[1:], here):
            full = os.path.join(here, path)
            if writes and run.generated(_git_path(tokens, here, full, path)):
                return (f"ship hook: Bash refused: git names {path}; ci/baselines/ and contracts/ change only through "
                        "the kit's generators")
            if is_git and not run.kit_owned(full):  # git reads name refs and paths; its writes are judged below
                if run.repo and inside(full, run.repo) and not run.may_write(full):
                    return f"ship hook: Bash refused: it names the main checkout ({path}); work only in your worktree"
                continue
            bad = path_problem(run, path, here, script)
            if bad:
                return f"ship hook: Bash refused: {bad}"
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


def _git_writes_tokens(tokens: list[str]) -> bool:
    names = [_name(t) for t in tokens]
    i = names.index("git") if "git" in names else names.index("git.exe")
    rest, j = tokens[i + 1:], 0
    while j < len(rest) and rest[j].startswith("-"):
        j += 2 if rest[j] in ("-C", "-c") else 1
    return j < len(rest) and _writes(rest[j], rest[j + 1:])


def _git_path(tokens: list[str], here: str, full: str, path: str) -> str:
    """A path a git command names, read from the folder git runs in (`-C`)."""
    names = [_name(t) for t in tokens]
    i = names.index("git") if "git" in names else names.index("git.exe")
    where = here
    rest = tokens[i + 1:]
    for j, t in enumerate(rest):
        if t == "-C" and j + 1 < len(rest):
            where = os.path.join(where, rest[j + 1])
        elif not t.startswith("-"):
            break
    return full if os.path.isabs(path) else os.path.join(where, path)


def decide(program: Program, event: dict) -> str | None:
    """None to allow, else the reason to refuse."""
    tool = event.get("tool_name", "")
    data = event.get("tool_input") or {}
    cwd = event.get("cwd") or os.getcwd()
    if tool not in FILE_TOOLS and tool != "Bash":
        return None
    try:
        run = Run(program)
    except Exception as exc:  # noqa: BLE001 - no role, an unknown role or an unreadable state.json refuses
        return f"ship hook: cannot tell what this worker may write ({exc!r}); refusing writes until it can"
    if tool in FILE_TOOLS:
        target = os.path.join(cwd, data.get(FILE_TOOLS[tool], ""))
        if run.kit_owned(target):
            return f"ship hook: {tool} to {target} refused; .kit/ is the kit's own folder and .desk/ the desk's"
        if run.builder_refused(target):
            return f"ship hook: {tool} to {target} refused; only the build loop writes a stop note"
        if run.generated(target):
            return (f"ship hook: {tool} to {target} refused; ci/baselines/ and contracts/ change only through the "
                    "kit's generators")
        if run.code_refused(target):
            return (f"ship hook: {tool} to {target} refused; role {run.role} writes no Python and no test or "
                    "packaging config (only builders do)")
        if run.may_write(target):
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
