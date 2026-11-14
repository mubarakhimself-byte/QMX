# <slice id>: <plain name>

<!--
How to fill (delete every comment when done). A builder works from this brief plus
PROJECT-RULES.md alone (and its generated slices/<id>/CHAIN.md packet), so anything it
needs to know goes here, including everything for its merge request (section 11): it
does no research. Use real values, never "appropriate" or "as needed". The fact blocks
below are a worked example from engine/base; replace them with this slice's own facts.
-->

Serves: S<n> in `SCOPE.md`. Stop point: <X>. Lane: <L1>. Depends on: <ids or none>.
Chain: <plan ids>; <A ids>; <E ids>; <X ids, or none>

## 1. Goal

<one line, in plain words: what is true for him after this slice that was not before>

## 2. Files it may touch

<the same list as this slice's row in SLICES.md, one per line, including forced files and why each is forced>

## 3. Facts about the code

<!--
Each fact is a fenced block: the opening line is three backticks, the word fact and an id;
the first body line is "$ " and one command; the rest is the exact expected output.
Add exit=N after the id when the command exits non-zero (git grep exits 1 on no match).
The dispatch script runs each fact in a fresh worktree at the build tip, with no shell
and no venv: no pipes, no redirections, no `uv run`. Prefer git grep, git show and
git log; use python -c for anything longer. Forward slashes in paths. Output is compared
after CRLF becomes LF and trailing spaces and blank lines go. Any mismatch parks the
slice as brief-mismatch, so check each fact at the tip before handing off.
-->

The unit's stop path lives in the node driver:

```fact F1
$ git grep -c "def close_frontier" -- qmn/src
qmn/src/qmn/loop/driver.py:1
```

The census this slice extends exists:

```fact F2
$ git grep -c "_CENSUS" -- qml/tests/test_unit_refuses.py
qml/tests/test_unit_refuses.py:2
```

## 4. Read first

- `<path>`: <what to learn there>
- Callers of `<symbol>`: `<path>`, `<path>` (found with `git grep -n "<symbol>("`)
- Intent: `<decision file and section>`

## 5. What it must do

1. <behaviour, with the real values: names, numbers, units, reason codes>
2. <...>

## 6. Tests that prove it

| Test | Door it calls | Fixture | Expected (literal) |
|---|---|---|---|
| `<package>/tests/test_<x>.py::test_<y>` | `<public function or command>` | <inputs> | `<exact value>` |

Each must fail at the parent on an assertion and pass at the head.

## 7. What it must not do

- <the nearby change it must leave alone, and why>
- <the fixed line it sits next to>
- Never rebuild: <each removed row (R id) touching these files, with its reason, or "no removed rows touch these files">

## 7a. Edge-case scenarios

From the planning funnel's self-annealing stage. Each line starts with its `E` id from `EDGE-CASES.md` and names the test that proves it; the checkpoint review walks each of them.

- <E id> <scenario>: <what must happen> (test: <test name from section 6, or "covered by fact X">)

## 8. Safety fact

<one sentence: the fact this slice is safe because of. The id is always SAFETY.>

`qml` reaches no keyring:

```fact SAFETY exit=1
$ git grep -n "keyring" -- qml/src
```

## 9. Done when

- [ ] Every item in 5 has a test from 6 that passes at the head.
- [ ] The safety fact gives the same output at the head.
- [ ] <slice-specific item>

Operations: <what this slice logs, how it is watched, what recovers it without a human> (test: <test name>), or "Operations: none, because <reason>".

## 10. Size guide

<S, M or L, with the expected order of changed lines. A guide, not a cap.>

## 11. Merge request

Everything the builder needs for the PR body (v2, `PR-BODY-AND-SKILLS-2026-11-12.md`), written by the planner so the builder does no research. The builder copies these lines and adds only the Summary and Evidence it produced.

- Title: <slice id>: <plain name>
- In plain words: <one or two sentences, no code names: what is true for him once this lands>
- TRACE: <slice id> -> <plan ids> -> <ask id>
- Door: <one-way | two-way>, because <reason>. Blast radius: <what else could break>, proved safe by fact SAFETY.
- DOC: <doc path> | <what changes in behaviour>, or "DOC: none"
- OPEN known at planning: <item | where | owner>, or "none"

Skills: <e.g. tdd, how>. Principles: <e.g. principle-subtract-before-you-add, principle-test-behavior-not-implementation>.
