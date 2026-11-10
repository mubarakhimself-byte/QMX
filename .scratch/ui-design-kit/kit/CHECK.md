# Kit double check (ticket 11)

Checked 2026-11-10 by a fresh agent that did not build the kit. What was read:
- this session's transcript `0a7a5e72…jsonl`, every line up to 13:08 UTC: user messages, queued mid-task messages, artifact-view wrappers, comments, and the lead's longer replies;
- `KIT.md`, `SOURCES.md`, `LEDGER.md`, `refs/his-words.md`, `refs/t3-code.md`, and the openings of the other refs.

Every path in KIT.md and SOURCES.md was tested on disk.

Overall the kit is in good shape. His words are complete. The ledger catches nearly every idea. Every path resolves. The findings below are refinements, plus three real gaps (C1 to C3).

## (a) Missing or misread items

### His words file (`refs/his-words.md`)

1. **No message is missing.** All 20 typed messages and the 3 sent mid-task (18:47, 07:19, 12:42) match the transcript paragraph by paragraph. There were no canvas comments. Nothing was added.
2. **M4 is junk, not a message.** "M4. 2026-11-10 13:07" holds a regex fragment (`\s*(.*?)\s*(?:`) that the extraction script picked up from its own source. It should be deleted. So the real count is 23, not the "24" the lead reported.
3. **M1 to M3 have no times.** Their headings read ". UTC". The times are:
   - M1: 2026-11-09 18:47;
   - M2: 2026-11-10 07:19;
   - M3: 2026-11-10 12:42.

   They arrived as queued messages, not inside tool results.

### Ideas missing from LEDGER/KIT, or read wrongly

| # | His words | Problem | Where it belongs |
|---|---|---|---|
| 1 | "I think let's leave the agent to tour it, because we might actually not use it. There are issues" (11-10 13:03, about T3 Code) | KIT calls T3 Code "his strongest current reference", and t3-code.md says "He picked T3 Code as the main reference". Neither one carries this later hedge. | KIT step 5 and the top of t3-code.md: a reference he may drop, "there are issues". |
| 2 | "Dribble, okay, Dribble is not a good one… Okay, Dribbble is one." (11-09 20:21) | LEDGER §1 records only "not a good one". He corrected himself in the next breath and counted Dribbble as a source. | LEDGER §1 inspiration line. |
| 3 | "my ruling for the ugly thing… overrules even the earliest opinions I had given" (11-09 18:40) | LEDGER §1 adds "(the concepts he liked still stand)". He never said that; it is the lead's reading. Usage A (§5) and Workflows B (§7) are both marked "decided", yet his "ugly" ruling covers all the canvas drafts. | Mark it as an interpretation. Note that §5 and §7 praise came before the ruling, so the concepts are open to re-test. |
| 4 | "these are skills. Okay, so we might change from aesthetics to design standards" (11-10 13:06) | Not captured anywhere. | KIT "Skills on hand" or LEDGER §1: the skills may move the work from taste toward design standards. |
| 5 | "you also have a component library because of the fact that QMX is extensible… things may be reused, things may be new" (11-09 17:51) | LEDGER only has the complaint "no components". The positive rule is missing: build a reusable component library, because QMX is extensible. | LEDGER §1 or §3. |
| 6 | "When you put it in feed format, this is interesting. This is very, very interesting." (11-09 18:40, Workflows) | Not captured. He liked the feed format over his usual "field" format. | LEDGER §7. |
| 7 | "of your own workflow, don't go based off what I said… use it as a baseline and iterate over it" (11-09 20:28) | Not captured. His process descriptions are a starting point, not the method. | KIT "The operator" or LEDGER §1. |
| 8 | "My taste is very… more advanced… Back then, it's just that it was the first time seeing my… tool have a face"; "I've looked at better UIs" (11-09 19:12) | Not in KIT. A new team should know his bar has risen since October, so October praise is a weak guide. | KIT "The operator". |
| 9 | "Have you tried connecting… the drop downs? Have you tried the threads?… What if the desktop application is different from the web?" (11-09 20:21); "having T3 code spawn up as a agent to see how it… represents [sub-agents]" (11-09 20:33); Theo's "Orchestrator V2" (20:28) | The T3 tour was closed as out of scope ("leave the agent to tour it"). KIT never says the tour is now the design team's job, or what is left: Usage, Source control, Worktrees, Environments, Devices, Threads, Labs, the desktop-vs-web differences and the sub-agent spawn test. The lead's v0.1.0 release-notes link for Orchestrator V2 was also dropped. | KIT, as a "To finish" line pointing at t3-code.md's last line. |
| 10 | "I think he's also using shadcn" (11-09 19:32, T3's web version) | A useful fact for a shadcn-svelte team. Not carried. | t3-code.md. |
| 11 | "The moment the sub-agent finishes, assume I'm not here… acknowledge it has finished and that's it" (M2) | A working-style rule the design sessions need, because they will run agents. | KIT "The operator". |
| 12 | LEDGER items cite "ticket 03", "ticket 06" and "ticket 07" as their owners | Those tickets were closed as out of scope (13:03). Their work now belongs to the design sessions. A new team can't act on a closed ticket. | LEDGER: change "ticket 0n" to "design sessions". |

Smaller drift, not worth separate rows:
- KIT says his Chrome "stays signed in" to Refero, Pinterest and X. He said the browser stays open overnight and "most are signed in".
- The lead promised that "the brief will point every session at [SOURCES.md] first" (12:56), but KIT lists it eighth. The source-beats-summary rule is still stated there.

### Lead facts that should carry, checked

- **Already carried:**
  - Agent SDK findings, including the Opus 5.5 todo-tools risk: grounding 03.
  - Workflows are engine documents (55 templates, 271 script steps, 17 agent steps), the desktop shell, the keyring bearer and Tauri: wiring-plan-draft and grounding 02.
  - The budget at 65% weekly on 11-09 night: overnight-plan-draft.
  - The mobile companion, and desktop vs web: LEDGER open decisions.
- **Contradicts his ruling:** `refs/grounding/05-ui-codebase.md` §7 ends with "Verdict: keep and evolve… Keep the codebase". On 11-10 at 12:28 he said, "it bothers me when you say it's worth keeping… it was never one." The file sits in the kit with no caveat. KIT doesn't list it, but a team that browses `refs/grounding/` will find it. It needs a header note saying the verdict is overruled and the file is facts only.

## (b) Broken paths

**None.** Every path tested exists:
- every relative link in KIT.md;
- every path in SOURCES.md: both transcripts, the zip, the storyboard, the October code and its notes, the screenshots, `D:/QMX-worktrees/*`, memory, the skill repos, the six installed skills, `JOURNEYS.md`, `launch.json`;
- the files behind the LEDGER source codes;
- the memory notes it cites.

`launch.json`'s `qmx-ui-design` points at the ui-review-repair folder, and its `node_modules/vite` exists, so the October UI should start. That was not run.

Not verified:
- The rejected canvas artifact link (claude.ai). The session's watch on it dropped with "connection lost".
- T3's web door `http://172.23.80.1:3773`. It needs a fresh pairing token from him each time, and that IP is a local adapter address that may change.

## (c) Gaps a new team would hit

1. **C1: Where does the design code go?** This is the biggest gap. KIT says to design in real shadcn-svelte code on `ui-redesign`. But `ui-redesign/apps/qmx-ui` is the stale 2026-10-01 stub. The October code lives only on `ui-review/repair`, and his ruling is that it is not a base. KIT doesn't say whether to:
   - start a fresh app;
   - copy the October tiling and theme engine;
   - or design in a sandbox route.

   This belongs in LEDGER's open decisions, or KIT should name it as the team's first call.
2. **C2: The kit isn't committed.** `.scratch/` is untracked on `ui-redesign` (`git status`: `?? .scratch/`). A clean-up or a worktree deletion would lose it. He should decide whether to commit it.
3. **C3: The skills are installed but never run.** The six Emil skills were only shown to load. Nobody ran them on a QMX screen, and their examples are React. He ruled "use the skills, not just read them" (11-09 20:33). The first design session should prove `variant-picker` and `break-ui` in Svelte before relying on them.
4. **No T3 Code screenshots.** The kit has only his usage-page image. The desktop app won't screen-capture, and the web door needs his pairing. Expect to ask him to pair at the start.
5. **Not in KIT:**
   - the shadcn-svelte **Rhea preset**, which is in his memory and the overnight draft;
   - the **phone companion** question, which is only in the LEDGER;
   - the overnight-plan draft, which holds the best summary of his long mandate, plus its budget and role facts. It is in `refs/` but not in the reading order.
6. **The build-and-wire brief is not written yet.** That's expected, since the map lists it as not yet specified. KIT's "After design" section is only a pointer.

## (d) What is solid

- **his-words.md** is complete and verbatim. Dictation noise is decoded, and both pasted images are present.
- **LEDGER.md** covers about 95% of his ideas across 16 areas:
  - statuses are honest, and lead proposals are marked open, not decided;
  - the 12 open decisions are the right ones (Lab, workflows-as-plugins, web door, pods, phone, neumorphism);
  - his reversals are caught (Portfolio softened, Claude Design dropped, overnight run cancelled, Fable left out of the brief).
- **The overnight mandate (msg 8) is well covered.** It shows up in LEDGER and in the overnight draft: orchestrator and Hindsight, the methodology session, DevOps layers, the shipped workflows, the Agent SDK check, budget, sequential agents, CIS, 118 PRs, QA at the end.
- **The rejected-drafts feedback (msg 3) is fully itemised:** feverish orange, uneven fonts, wasted space, big buttons, too many words, no icons or components, the "vomit" trading node, the poor Lab declutter.
- **october-ui-trace.md** is rigorous. It ties each idea to his quote, the storyboard and the screenshot, and it finds the never-used Factory settings reference.
- **SOURCES.md** meets his 12:56 ask that the team can reach every original. Every path is live.
- **KIT.md** makes no design decision on his behalf. Its "rejected" list and the stack line match his words.
