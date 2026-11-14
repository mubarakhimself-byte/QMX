# Slices: <program>

<count> slices for <n> asks, because <why this count follows his asks: one slice per piece of behaviour he can see, plus any slice a shared file forces>.

Checkpoints: <A: n slices, B: n slices, ...>. Lanes: <how many builders can run at once, and why the lanes split where they do>.

| id | name | ask | stop | lane | depends on | files | size |
|---|---|---|---|---|---|---|---|
| <prefix>-01 | <plain name> | S1 | A | L1 | - | <path>, <folder>/, <glob> | M |

<!--
How to fill (delete this comment when done):
- The scripts read the FIRST table holding the columns id, name, depends on, files, size,
  by column name. Keep this table first; ask, stop and lane are extra columns the scripts
  ignore and the coordinator, plan review and the checks read. Never paste an example
  table above this one.
- id: unique across every program, because worktrees are named <worktree_root>/slice-<id>
  and branches slice/<id>. Use a program prefix registered in standing/PREFIXES.md. A
  stop-point fix program uses <prefix>-<stop>-fix-<n>.
- ask: the S-number from SCOPE.md this slice serves. No ask means it is a proposal.
- stop: the checkpoint (stop point) from PROGRAM.yaml. A checkpoint is where review runs
  and the work merges. Aim for 5 to 8 slices, each checkpoint a coherent piece the review
  can judge against the plan and ending in something he can see. More than 8 is split
  (A1, A2). This is a guide the checks warn on, never a refusal.
- lane: who does what. Slices in different lanes of the same checkpoint share no files,
  so their builders run at once. A lane is worked in order, so a dependency inside a lane
  is fine; one across lanes makes a builder wait. Lanes of the next checkpoint should
  avoid the files of the one before, so they can be built while that one is reviewed.
- depends on: comma list of ids, or -. Two slices whose files overlap need an edge or the
  same lane; the dispatch script refuses overlapping slices at once anyway.
- files: comma list of paths, folders (dir/ or dir/**) and globs (*, ?, **), forward
  slashes, no commas inside a path. Include the files the change forces: pins, counts,
  census rows, schema copies, reason-code lists, version rows, app.toml, uv.lock when a
  pyproject changes. verify_ready refuses a READY whose changed files fall outside this list.
- size: S, M or L. A guide for the build, not a cap.
- Growth: when the slices per ask pass the growth setting in check_chain.py, add a line
  "Growth: <why each extra slice is needed>" above the table. Splitting only to split is
  not a reason.
- After the run starts (ship init), this table never changes. A changed row means a new
  program folder.
-->
