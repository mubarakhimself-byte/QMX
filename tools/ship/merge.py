"""ship merge: land a clean checkpoint into the target branch as a script (unit U10, FACTORY-DESIGN 2.8).

`merge(program, stop, settings)`; every step is safe to run twice:

1. Already merged (the stop recorded in `state.merged` and `merge/<X>.md` holding `MERGED`, or `EMPTY`): 0.
2. Every `VERDICT: BLOCKED` under `stop-review/<X>/` and the fix folder's is followed by a later CLEAN;
   otherwise WAITS, 10. The reviewed tip is the END sha of the latest CLEAN (REVIEW-2.md before REVIEW.md).
3. The remote build branch is at the reviewed tip, or at the `MERGE-BASE` this script recorded; else
   WAITS, 10.
4. When the build tip does not contain the target tip (another program merged first), the target is
   merged into the build branch in a frozen checkout (`git merge --no-ff`, subject `merge: ...`), any
   `uv.lock` the merge touched is regenerated with `lock_cmd`, the commit is pushed and written to
   `merge/<X>.md` as `MERGE-BASE <sha>`, and a deep run on it is awaited. A conflict or a red run
   writes a one-slice fix program `<program>-fix-<X>` (slice `<prefix>-<X>-fix-merge`, files: the
   conflicted paths) and returns 2; when that folder already exists (round 1 used it), there is no
   third round: WAITS, 2.
5. The open PR from the build branch into the target is reused, or created from `merge/<X>-pr.md`
   (written by the verdict worker; missing: WAITS, 10).
6. `ci.gate` on the PR, waited for: not green is WAITS with the lines, 2; still pending at the wait
   limit or GitHub unreachable is 3.
7. `gh pr merge <pr> --merge`; GitHub's refusal is WAITS, 2. Then the merged tip must be an ancestor
   of `origin/<target>`.
8. `merge/<X>.md` gets the PR, the reviewed tip, the target sha, the deep run's lines and
   `MERGED <target sha>`; the stop is recorded merged; the stop's rows of the program's `REMOVED.md`
   move to `_records/REMOVED.md` with `Status: removed <sha>`, under `records.lock`, in one commit.

The target is the setting `ci_gate_base` (the branch the checkpoint PR targets). Exit: 0 merged or
already merged, 2 refused by the gate or a fix program written, 3 unreachable (try again), 10 waits.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from ship import ci
from ship import phase
from ship import program as prog
from ship import state as st
from ship.gitx import GitError, git, git_rc, is_ancestor, remote_sha
from ship.layout import Program, records_of
from ship.plan import PlanError, parse_slices
from ship.review import add_wait, checkpoint_key
from ship.settings import Settings
from ship.trace import R_ID, brief_text
from ship.worktree import checkout_copy, drop_copy
from ship.wrapper import run_timed

MERGED = re.compile(r"^MERGED\s+([0-9a-f]{7,40})", re.M)
MERGE_BASE = re.compile(r"^MERGE-BASE\s+([0-9a-f]{40})", re.M)
LOCK_INPUTS = ("pyproject.toml", "uv.lock")


class Unreachable(Exception):
    pass


class Merge:
    def __init__(self, program: Program, stop: str, settings: Settings):
        self.program, self.stop, self.settings = program, stop, settings
        self.state = st.load(program)
        self.repo = Path(self.state.repo)
        self.target = settings.ci_gate_base
        self.note = program.merge_note(stop)
        self.lines: list[str] = []
        self.t = settings.git_timeout_s

    def say(self, line: str) -> None:
        self.lines.append(line)

    def wait(self, text: str, see: str = "", detail: str = "") -> int:
        add_wait(self.program, text, see or str(self.note), detail)
        self.say(f"WAITS {text}")
        return 10

    def note_text(self) -> str:
        return self.note.read_text("utf-8") if self.note.exists() else ""

    # -- the steps --

    def run(self) -> int:
        text = self.note_text()
        key = checkpoint_key(self.state, self.stop)
        if re.search(r"^EMPTY\b", text, re.M):
            self.say(f"EMPTY stop {self.stop} closed with no commits")
            return 0
        if MERGED.search(text):
            if key not in self.state.merged:
                self.record_merged(key)
            self.say(f"ALREADY stop {self.stop} merged: {MERGED.search(text).group(1)}")
            return 0
        reviewed = self.reviewed_tip()
        if reviewed is None:
            return 10
        try:
            git(self.repo, "fetch", "-q", self.state.remote, timeout=self.t)
            build_tip = remote_sha(self.repo, self.state.remote, self.state.build_branch, self.t)
            target_tip = remote_sha(self.repo, self.state.remote, self.target, self.t)
        except GitError as exc:
            raise Unreachable(str(exc)) from exc
        merge_base = MERGE_BASE.search(text)
        if build_tip not in (reviewed, merge_base.group(1) if merge_base else None):
            return self.wait(f"stop {self.stop}: the build branch is at {str(build_tip)[:10]}, not the reviewed "
                             f"tip {reviewed[:10]}; nothing merged")
        if not target_tip:
            return self.wait(f"the target branch {self.target} is not on {self.state.remote}")
        if is_ancestor(self.repo, build_tip, target_tip, self.t):
            self.say(f"ON-TARGET {build_tip[:10]} is already in {self.target}")
            return self.finish(key, reviewed, build_tip, None, target_tip)
        if not is_ancestor(self.repo, target_tip, build_tip, self.t):
            got = self.merge_target(build_tip, target_tip)
            if isinstance(got, int):
                return got
            build_tip = got
        if not self.deep_green(build_tip):
            return self.fix_program(build_tip, [], f"the deep run on {build_tip[:10]} is red")
        pr = self.pull_request()
        if pr is None:
            return 10
        rc, lines = ci.wait(lambda: ci.gate(self.program, self.settings, pr), self.settings)
        self.lines += lines
        if rc == 1:
            add_wait(self.program, f"stop {self.stop}: the merge gate refused PR {pr}", str(self.note),
                     "\n".join(lines))
            return 2
        if rc != 0:
            raise Unreachable(f"the gate on {pr} did not finish: {'; '.join(lines)}")
        try:
            ci.Gh(self.settings, self.repo).call("pr", "merge", pr, "--merge")
        except GitError as exc:
            try:
                remote_sha(self.repo, self.state.remote, self.target, self.settings.net_timeout_s)
            except GitError as down:
                raise Unreachable(str(down)) from exc
            add_wait(self.program, f"stop {self.stop}: GitHub refused to merge {pr}", str(self.note), ci.short(exc))
            return 2
        try:
            git(self.repo, "fetch", "-q", self.state.remote, timeout=self.t)
            target_tip = remote_sha(self.repo, self.state.remote, self.target, self.t)
        except GitError as exc:
            raise Unreachable(str(exc)) from exc
        if not target_tip or not is_ancestor(self.repo, build_tip, target_tip, self.t):
            add_wait(self.program, f"stop {self.stop}: {pr} says merged, but {build_tip[:10]} is not in "
                                   f"{self.target}", str(self.note))
            return 2
        return self.finish(key, reviewed, build_tip, pr, target_tip)

    def verdicts(self) -> list[tuple[str, str, Path]]:
        """(word, END sha, file) in review order: round 1, round 2, then the fix folder's own."""
        fix = self.program.dir.parent / f"{self.program.dir.name}-fix-{self.stop}"
        files = [self.program.stop_review(self.stop) / "REVIEW.md", self.program.stop_review(self.stop) / "REVIEW-2.md",
                 fix / "stop-review" / self.stop / "REVIEW.md", fix / "stop-review" / self.stop / "REVIEW-2.md"]
        out = []
        for path in files:
            word, end = phase.verdict(path)
            if word:
                out.append((word, end, path))
        return out

    def reviewed_tip(self) -> str | None:
        found = self.verdicts()
        if not found:
            self.wait(f"stop {self.stop} has no verdict to merge on", str(self.program.stop_review(self.stop)))
            return None
        for n, (word, _, path) in enumerate(found):
            if word == "BLOCKED" and not any(w == "CLEAN" for w, _, _ in found[n + 1:]):
                self.wait(f"stop {self.stop}: {path.name} is BLOCKED with no later CLEAN", str(path))
                return None
        word, end, path = found[-1]
        if word != "CLEAN" or len(end) != 40:
            self.wait(f"stop {self.stop}: the last verdict {path.name} is not a CLEAN with a full END sha", str(path))
            return None
        return end

    def merge_target(self, build_tip: str, target_tip: str) -> str | int:
        """Merge the target into the build branch; the pushed commit, or an exit code."""
        copy = checkout_copy(self.repo, self.program.tmp / "merge", build_tip, self.settings)
        try:
            message = f"merge: {self.target} into {self.state.build_branch} for stop {self.stop}"
            rc = git_rc(copy, "merge", "--no-ff", "--no-edit", "-m", message, target_tip, timeout=self.t)
            locks: set[str] = set()
            if rc != 0:
                unmerged = git(copy, "diff", "--name-only", "--diff-filter=U", timeout=self.t).split()
                if unmerged and all(PurePosixPath(f).name == "uv.lock" for f in unmerged):
                    git(copy, "checkout", "--ours", "--", *unmerged, timeout=self.t)
                    git(copy, "add", "--", *unmerged, timeout=self.t)
                    git(copy, "commit", "-q", "--no-verify", "--no-edit", timeout=self.t)
                    locks |= {str(PurePosixPath(f).parent) for f in unmerged}
                else:
                    git(copy, "merge", "--abort", timeout=self.t, check=False)
                    self.say(f"CONFLICT merging {self.target} {target_tip[:10]}: {unmerged}")
                    return self.fix_program(build_tip, unmerged or ["(the merge)"],
                                            f"merging {self.target} conflicts in {unmerged}")
            touched = git(copy, "diff", "--name-only", build_tip, "HEAD", timeout=self.t).split()
            locks |= {str(PurePosixPath(f).parent) for f in touched if PurePosixPath(f).name in LOCK_INPUTS}
            if locks and not self.regenerate_locks(copy, locks):
                return self.wait(f"stop {self.stop}: uv.lock could not be regenerated after merging {self.target}")
            new = git(copy, "rev-parse", "HEAD", timeout=self.t).strip()
            try:
                git(copy, "push", "-q", self.state.remote, f"HEAD:refs/heads/{self.state.build_branch}", timeout=self.t)
            except GitError as exc:
                raise Unreachable(f"push of the merge commit: {exc}") from exc
        finally:
            drop_copy(self.repo, copy, self.settings)
        text = self.note_text()
        text = MERGE_BASE.sub("", text).strip()
        self.note.parent.mkdir(parents=True, exist_ok=True)
        self.note.write_text((text + "\n" if text else "") + f"MERGE-BASE {new}\n", "utf-8", newline="\n")
        self.say(f"MERGE-BASE {new}: {self.target} {target_tip[:10]} merged into {self.state.build_branch}")
        return new

    def regenerate_locks(self, copy: Path, dirs: set[str]) -> bool:
        changed = False
        for d in sorted(dirs):
            if not (copy / d / "pyproject.toml").exists() and not (copy / d / "uv.lock").exists():
                continue
            log = self.program.tmp / "merge-logs" / f"lock-{d.replace('/', '-') or 'root'}.log"
            if run_timed(list(self.settings.lock_cmd), copy / d, log, self.settings.check_timeout_s, self.settings,
                         self.program.runs).rc != 0:
                return False
            git(copy, "add", "--", str(PurePosixPath(d) / "uv.lock"), timeout=self.t)
            changed = True
        if changed and git(copy, "diff", "--cached", "--name-only", timeout=self.t).strip():
            git(copy, "commit", "-q", "--amend", "--no-edit", "--no-verify", timeout=self.t)
        return True

    def deep_green(self, tip: str) -> bool:
        """A green deep run is recorded for `tip`, or one is run now and waited for."""
        fresh = st.load(self.program)
        deep = fresh.ci.get("deep") or {}
        if (deep.get("tip") == tip and deep.get("result") == "green") or fresh.last_green == tip:
            return True
        from ship.nightly import nightly

        ok, lines = nightly(self.program, self.settings, wait=True)
        self.lines += lines
        if ok is None:
            raise Unreachable(f"the deep run on {tip[:10]} did not finish")
        return bool(ok)

    def pull_request(self) -> str | None:
        gh = ci.Gh(self.settings, self.repo)
        try:
            listed = gh.prs(self.state.build_branch, self.target)
        except GitError as exc:
            raise Unreachable(str(exc)) from exc
        if listed:
            self.say(f"PR {listed[0]['url']} reused")
            return str(listed[0]["url"])
        body = self.program.dir / "merge" / f"{self.stop}-pr.md"
        if not body.exists():
            self.wait(f"stop {self.stop}: the PR body {body.name} is missing; the verdict worker writes it", str(body))
            return None
        title = f"{self.program.dir.name} stop {self.stop}: {self.done_when()}"
        try:
            url = gh.call("pr", "create", "--base", self.target, "--head", self.state.build_branch, "--title", title,
                          "--body-file", str(body)).strip().splitlines()[-1]
        except GitError as exc:
            raise Unreachable(str(exc)) from exc
        self.say(f"PR {url} created")
        return url

    def done_when(self) -> str:
        try:
            stops = prog.load(self.program).stops if self.program.project_file.exists() else []
        except prog.ProgramError:
            stops = []
        return next((s.done_when for s in stops if s.id == self.stop and s.done_when), "checkpoint")

    def finish(self, key: str, reviewed: str, merged_tip: str, pr: str | None, target_tip: str) -> int:
        deep = self.program.nightly(merged_tip) / "summary.txt"
        deep_lines = deep.read_text("utf-8").splitlines() if deep.exists() else ["(no deep run summary here)"]
        body = [f"# Merge of {self.program.dir.name} stop {self.stop}", "", f"PR: {pr or '(already on the target)'}",
                f"Reviewed tip: {reviewed}", f"Merged tip: {merged_tip}", f"Target: {self.target} {target_tip}", "",
                "Deep run:", *[f"    {x}" for x in deep_lines[-20:]], ""]
        base = MERGE_BASE.search(self.note_text())
        if base:
            body.append(f"MERGE-BASE {base.group(1)}")
        body.append(f"MERGED {target_tip}")
        self.note.parent.mkdir(parents=True, exist_ok=True)
        self.note.write_text("\n".join(body) + "\n", "utf-8", newline="\n")
        self.record_merged(key)
        self.lines += self.move_removed(target_tip)
        self.say(f"MERGED stop {self.stop} into {self.target} at {target_tip}")
        return 0

    def record_merged(self, key: str) -> None:
        try:
            with st.locked(self.program) as state:
                self.say(state.mark_merged(key))
        except st.StateError as exc:
            add_wait(self.program, f"stop {self.stop} merged but state.json refused to record it: {exc}", str(self.note))
            self.say(f"WAITS {exc}")

    def stop_slices(self) -> set[str]:
        return {s.id for s in self.state.slices.values() if (s.checkpoint or self.stop) == self.stop}

    def move_removed(self, sha: str) -> list[str]:
        """The stop's rows of the program's REMOVED.md go to _records/REMOVED.md, removed at `sha`."""
        from ship import records

        own = self.program.dir / "REMOVED.md"
        if not own.exists():
            return []
        mine = self.stop_slices()
        texts = [brief_text(self.program, sid) for sid in mine]
        lines = own.read_text("utf-8").splitlines()
        moving = [ln for ln in lines if R_ID.search(ln) and any(r in t for r in R_ID.findall(ln) for t in texts)]
        if not moving:
            return []
        plans = self.program.dir.parent
        rec = records_of(plans)
        if not rec.removed.exists():
            return [f"NOTE no {rec.removed}; {len(moving)} removal rows stay in {own}"]
        done = [re.sub(r"Status:\s*planned\b.*$", f"Status: removed {sha}", ln) for ln in moving]
        if not any("Status:" in ln for ln in moving):
            done = [f"{ln} Status: removed {sha}" for ln in moving]
        out = []
        with records.locked(rec):
            old = rec.removed.read_text("utf-8")
            new_rows = [ln for ln in done if ln not in old.splitlines()]
            if new_rows:
                rec.removed.write_text(old.rstrip("\n") + "\n" + "\n".join(new_rows) + "\n", "utf-8", newline="\n")
            own.write_text("\n".join(ln for ln in lines if ln not in moving) + "\n", "utf-8", newline="\n")
            sha_ = records.commit(plans, f"records: removed rows of {self.program.dir.name} stop {self.stop}",
                                  self.settings, remote=self.state.remote, lines=out)
        return out + [f"REMOVED {len(moving)} rows to _records/REMOVED.md" + (f" in {sha_[:8]}" if sha_ else "")]

    def fix_program(self, tip: str, paths: list[str], why: str) -> int:
        """A one-slice fix program that does the merge (section 6, rows 30 and 48)."""
        fix = Program(self.program.dir.parent / f"{self.program.dir.name}-fix-{self.stop}")
        if fix.project_file.exists():
            return self._no_third_round(fix, why)
        files = [p for p in paths if p and not p.startswith("(")]
        if not files:
            try:
                base = self._stop_from()
                files = git(self.repo, "diff", "--name-only", base, tip, timeout=self.t).split() if base else []
            except GitError:
                files = []
        files = files or ["(the merge commit)"]
        sid = f"{self.prefix()}-{self.stop}-fix-merge"
        target_tip = remote_sha(self.repo, self.state.remote, self.target, self.t) or ""
        fix.dir.mkdir(parents=True, exist_ok=True)
        fix.project_file.write_text(
            f"project: {self._project()}\nprogram: {fix.dir.name}\nkind: fix\nparent: {self.program.dir.name}\n"
            f"build_branch: {self.state.build_branch}\nparent_tip: {tip}\n"
            f"gates:\n  go: {{by: stop-review, at: {st.now_iso()[:10]}, source: \"merge/{self.stop}.md\", "
            f"advance: yes}}\nstop_points:\n  - id: {self.stop}\n    tier: core\n    handoff: ready\n",
            "utf-8", newline="\n")
        fix.slices_md.write_text(
            "| id | name | stop | depends on | files | size |\n|---|---|---|---|---|---|\n"
            f"| {sid} | Merge {self.target} into the build branch | {self.stop} | - | {', '.join(files)} | S |\n",
            "utf-8", newline="\n")
        brief = fix.brief(sid)
        brief.parent.mkdir(parents=True, exist_ok=True)
        brief.write_text(
            f"# {sid}: merge {self.target} into {self.state.build_branch}\n\n"
            f"Serves: the parent's asks. Stop point: {self.stop}. Kind: feature. Depends on: none.\n"
            f"Chain: merge of stop {self.stop}; none; none; none\n\n## 1. Goal\n\n"
            f"{self.target} ({target_tip[:10]}) is merged into {self.state.build_branch} and everything is green: {why}.\n\n"
            f"## 2. Files it may touch\n\n" + "".join(f"{f}\n" for f in files) +
            f"\n## 3. Facts about the code\n\n```fact SAFETY\n$ git cat-file -t {target_tip}\ncommit\n```\n",
            "utf-8", newline="\n")
        for name in ("checks.toml", "ship.toml"):
            src = self.program.dir / name
            if src.exists():
                (fix.dir / name).write_text(src.read_text("utf-8"), "utf-8", newline="\n")
        add_wait(self.program, f"stop {self.stop}: {why}; a fix program does the merge (round 2 follows)",
                 str(fix.dir))
        self.say(f"FIX {fix.dir.name}: {sid} on {files}")
        return 2

    def _no_third_round(self, fix: Program, why: str) -> int:
        add_wait(self.program, f"stop {self.stop}: {why}, and its fix program was already used; there is no third "
                               "round", str(fix.dir))
        self.say(f"WAITS no third round: {why}")
        return 2

    def _stop_from(self) -> str:
        try:
            from ship.trace import stop_range

            return stop_range(self.program, self.stop)[0]
        except Exception:  # noqa: BLE001 - a fix program can be written without it
            return ""

    def _project(self) -> str:
        try:
            return (prog.load(self.program).project if self.program.project_file.exists() else None) or "qmx"
        except prog.ProgramError:
            return "qmx"

    def prefix(self) -> str:
        try:
            ids = [s.id for s in parse_slices(self.program.slices_md.read_text("utf-8"))]
        except (OSError, PlanError):
            ids = []
        heads = [i.split("-", 1)[0] for i in ids if "-" in i]
        return heads[0] if heads else self.program.dir.name


def merge(program: Program, stop: str, settings: Settings) -> tuple[int, list[str]]:
    job = Merge(program, stop, settings)
    try:
        rc = job.run()
    except Unreachable as exc:
        job.say(f"UNREACHABLE {exc}; nothing more changed, try again later")
        rc = 3
    return rc, job.lines
