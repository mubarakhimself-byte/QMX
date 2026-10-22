# Open decisions (what is still his; the design proceeds on the recommendation)

## After the data round (2026-10-22, `research/methodology/55-data-round-architecture.md`)

- **W4. Settled by his answers (rulings 120-134).** The data hold of rulings 91 and 111 is lifted: he answered the funnel's questions (Library as the one catalog, the server as the main copy this week, free sources first, OpenObserve's free tier) and gave no further data seeds. The architecture pass decided the rest without him (AD-67 to AD-70; Library AD-25 to AD-33; Lab AD-19, AD-20).
- **W5. Still his, two small calls** (55 §12): open a cloud bucket for the off-server copy (recommend a Cloudflare R2 bucket, about $2-3 a month at today's sizes; money), and allow removing the old 10 GB from his C: drive once two checked copies exist (recommend yes; irreversible on his machine). Nothing else in the data round waits on him; packet DR0 copies to the server first, and the bucket joins when it exists.
- **W3 applied.** The order-word matcher's call sites go (AD-59 amended: three call sites, not two), then the harness's own copy (HARNESS-REQUESTS H62).

## After review 48 (2026-10-18, `research/methodology/48-review-unlocked-and-folded.md`)

- **W3. Settled 2026-10-18 by the planning lead from rulings 115-118 (not his call).** He ruled agents have no path to money and that money-safety machinery is over-engineering, then unlocked the whole app (118). So the old order-word money gate goes and the guard (AD-54) stays as ordinary hygiene: sign-ins, keys, QMX's own databases and destructive commands.

## After the studies-folded pass (2026-10-18, `research/methodology/47-studies-folded.md`)

The pass decided every design change in studies 44, 45 and 46 without him, and recorded his choice of Hindsight as ruling 119. Two questions about words stay his (study 45); the design proceeds without them and nothing waits:

- **W1. Does "strategy" stay a word you use?** The risk session owns "unit", the Library shows bots, and `strategy` today is the stored mirror of a strategy family. Recommend: keep it only as the name of a family of bots in the Library; say "bot" for the thing that trades.
- **W2. Is one folder shape with two names fine?** A mini app (something you use: screens, actions, its own saved state) and an agent (a persona with its own instructions, skills and routines) are built the same way. Recommend: yes, keep both names.

Two more words have defaults he may change at any time (study 46): the shelf of hypotheses is called "Ideas"; "forget" hides a memory from every recall and keeps an archived copy he can restore (only a pasted secret is truly removed).

## After the unlock pass (2026-10-18, ruling 118)

Ruling 118 unlocked the whole app, the harness included. So the two harness rounds that waited for his yes (D and G below) are no longer his calls: they are ordinary design changes, decided in `research/methodology/43-whole-app-unlocked.md` and listed in `HARNESS-REQUESTS.md` (now a plain change list). The only call still his:

1. **Which rented provider to pay for, and when** (money; nothing is paid for yet, ruling 69). Recommend: decide only when your Contabo server's four agent slots overflow too often; adding a provider needs no code (AD-30).

Not a call, and nothing waits on it: the fifth quant lens (ruling 112) is still yours to name; nothing is built on it.

Closed by the unlock pass:
- *D, the small harness tidy-up round:* done as plain changes (HARNESS-REQUESTS sections B and I).
- *G, the harness changes for helpers on other providers and the rest of the rerun's harness rows:* done as plain changes (sections D, E, G). The native-helpers part under a Claude-plan main still waits on probe P1, because that rests on what the Claude Code program does, not on a permission.

## After the retirement pass (2026-10-18, rulings 115-117) — superseded by the section above

These were the calls still his before ruling 118. D and G are closed above; 1 is unchanged.

D. **Approve a small harness tidy-up round** (it used to be called HG3). After the retirement pass it holds only items that fix bugs or tidy up; nothing in it is a safety fence any more:
   1. Each workflow step gets exactly the tools it says it needs, and a one-shot AI step gets none. Today a resumed step can still use tools it was told not to use.
   2. A helper chat that has finished is closed, so its program stops. Nothing is deleted.
   3. A chat keeps its early-summary point and its event hooks when QMX restarts.
   4. The harness package says it is typed, so the rest of QMX type-checks without a workaround.
   5. The record says who acted: your click, or the copilot's call. It is a label, not a lock.
   6. Five harness bugs from the first build: the usage check stops spending an extra small AI call on every later call; it tidies up before closing a chat; a chat's saved options are dropped when the chat ends; one cancel error is caught; the runs list stops showing chats as agent runs.
   **Recommend: yes.** If no: each item has a workaround with no harness change; AI steps are told in words to use no tools and fail if they do.

G. **Approve the harness changes that let your copilot use Kimi, Qwen and other providers as helpers** (your ruling 92). Two changes do it, and either one alone already works:
   - *Native helpers on other providers.* The harness gains one new option per chat: a list of named helpers (one per role, plus any model you pin in Settings, such as a Kimi reviewer), built from QMX's model list and handed to the Claude SDK when the chat starts. The main agent's own helper tool can then start a helper on Kimi or Qwen directly. The list is rebuilt each time the chat restarts and leaves out any helper whose provider the chat cannot reach right now. For a main agent on your Claude plan it ships only after one test under your real Claude sign-in proves the helper's model name reaches the provider; for a main agent on Kimi or GPT a test with a key is enough. (Reference: H38.)
   - *The new delegate.* The harness's `delegate` tool is rebuilt. Starting a helper returns a ticket at once instead of making the main chat wait; several helpers run at the same time; the main chat can list, steer and stop them; each helper's result is saved first and then handed to the main chat between its turns, so nothing is lost if the main chat is busy; a helper can be a chat on any provider, or an outside agent program (such as OpenCode) that runs on your PC as an ordinary program and sends its model calls through QMX's router. Running that program in a container or on your server is your option, not a rule. (Reference: H26.)
   The same round also asks for the other harness items the rerun listed (attachments on turns, your own always-allow and never-allow rules, per-session tool packs, standing copilot loops, browser and screen-reading tools, the background review fork, and a one-shot AI call without starting a CLI). **Recommend: yes to all.** If both helper changes were refused, the copilot could still use other providers through today's `delegate`, one helper at a time, waiting for each.

1. **Which rented provider to pay for, and when** (money; nothing is paid for yet, ruling 69). Recommend: decide only when your Contabo server's four agent slots overflow too often; adding a provider needs no code (AD-30).

**Closed by the retirement pass:**
- *Old E, "edited and AI-written scripts never run bare on the PC": answered NO* (rulings 115-117). Scripts and agents run on your PC as ordinary programs, the way Claude Code does. A container, your server or a rented machine is your choice per workflow, never a safety rule. The sealed Windows box, the shipped-file check and Docker-first start-up are retired (AD-24).
- *Old F, "a money scan that fails closed with no allow-list": retired* (AD-36). Agents have no path to money, so no scan of scripts and prompts for money words is built. The money-word check that already exists in the built workflow checker stays as it is and is not extended.
- The five-step MT5 and cTrader demo proof is retired: agents use the demo accounts you set up; live accounts are never in their reach (AD-33). The alarm for a stolen step pass is retired; passes still expire with their step (AD-28).

Earlier record, 2026-10-18 evening (the rerun): Closed by the rerun (architect's calls under ruling 98 and the operator's brief; recorded in `methodology/39`): the routing option (A + B + D, AD-38); old **B** text (no usage caps, AD-40, settled); old **0** (folded into E with the corrected count of five); old **2** `host_harness` (allowed as a leaf attempt with key accounts; he removes a provider from `runs_on` if he wants every transcript on his machines); old **3** plan logins on Contabo and an owned Amp runner (yes; he signs in once on each with `qmx node login`); old **4** irreversible external effects (the recommended list stands: messages, posts, webhooks, outbound calls to non-QMX systems, desktop actions that submit or send, app operations an app marks so).


Refreshed 2026-10-16 night against rulings 73-88 (27c gap fixes). The three calls at the top are his; everything below them is either still open with a recommendation, or closed with the ruling that closed it.

## After the first build run (2026-10-18) — superseded

**Superseded by the section above (41 L4).** D, E and F below are the older framings; the rerun's D, E and F at the top replace them word for word (in particular, the old E's "waits with 'Docker is off'" is gone: QMX starts Docker, then spills to Contabo, and waits only when neither works). Kept for the record only.

The calls A, B and C below are closed: A by ruling 89 (H0, H15, H16, H17 granted and built as HG1), B by ruling 90 (every account carries its own configurable background share; 50 % is only a default; **itself superseded** on 2026-10-18 by AD-40: no default share at all, only a value he sets), C by ruling 91 (data is held until a deeper data study). The amendment after the run (`methodology/35`) adds these:

D. **Grant the HG3 harness round** (HARNESS-REQUESTS H2 re-asked, H18-H25, plus five harness bug fixes). **Recommend: yes, H2 first.** H2 is the one with a security reason: until an engine agent chat can be started without the built-in `Bash`, `Write`, `Edit` and `NotebookEdit`, agent nodes on the PC depend on an ask the engine rejects (AD-24, live check E35), and are held if that ask does not come. The rest are tidiness and cost (closing chats, a cached brief, no asks for draft saves, typing, a public `ControlService`, telling his clicks from the copilot's calls, chat routes for the engine host).

E. **Accept that edited workflows need Docker Desktop running** (AD-24). Only scripts byte-identical to what QMX shipped may run on the PC directly, and even those run inside a Windows AppContainer that cannot see his plan login, his keyring or QMX itself. A template he or the copilot edited runs its scripts in a container, so with Docker off it waits with "Docker is off" instead of running. **Recommend: yes.** Ruled the other way: edited scripts would run on the host inside the AppContainer too, which trusts the AppContainer alone for code nobody reviewed.

F. **Accept a money scan that fails closed with no allow-list** (AD-36). It reads every script, prompt, name and note for call-shaped money verbs with the harness gate's own matcher. It will sometimes refuse an innocent sentence ("write the order of the sections" reads as "write order"), and the fix is to reword. **Recommend: yes.** Ruled the other way: a reviewed allow-list of phrases, which is one more thing a model could try to widen.

## Calls for him first (closed, kept for the record)

A. **Harness grants H0, H15, H16, H17** (HARNESS-REQUESTS). H0 exports `Background` and `Child` from `qma/harness/__init__.py`; H17 adds `AGENT_OPERATIONS` table rows for the new engine, Library and Lab tools (draft save and test run are `DOMAIN_WRITE`, so they never ask; publish, enable and live runs are `MANAGE`, so they ask once); H15 is a per-chat compaction threshold and H16 per-chat hooks for Background chats. None is inside ruling 39's load-balancer exception, so ruling 24 needs his explicit yes. **Recommend: yes to all four.** H0 and H17 are export-only and table-row edits; H15 and H16 are what ruling 78 calls critical. Each has a fallback with no harness edit (a narrow import allow-list; draft saves through `library_save` plus a test-on-save watcher; an engine-driven compaction restart; tool spans read from session blocks), so a "no" slows the build but does not block it.

B. **Does the harness's 50 % plan background cap still apply to workflow agent nodes, given ruling 27** (no spending caps, no asking about usage)? Today a Background chat on the plan is refused at 50 % of the window (`QH/launch.py:182-188`). **Recommend: keep it for plan accounts only**, so his own copilot always has half the plan; key-provider accounts have no such cap, and the engine's admission control waits quietly at the cap instead of asking (SOLUTION-DESIGN §7.4). Ruled the other way: workflows may use the whole plan window, and his copilot can find it empty.

C. **Accept study 30 for the first data packets** (rulings 58, 81: data is among the first things built; tick backup and import are early work). No architecture owns the market-data service, the tick backup or the import of the orphaned ~10 GB history; study 30 §4-§5 designs them. **Recommend: accept study 30 §4-§5 as the binding design for the first data packets** (back up the 10 GB first, one ingest path, `qmx-marketdata` on Contabo, `dataset` cards in the Library) and schedule them first. Ruled the other way: a short spine pass on data runs before any data packet.

## Older list (closed by the rerun and the retirement pass; kept for the record)

0. (Closed: retired with old E, rulings 115-117.) **Whether the two templates that read the network (DB's calendar, T4's central-bank feeds) keep running `host_confined` with `network: true`, or move to the container tier** (AD-24). Recommend: keep them `host_confined` while they are byte-identical to the shipped pack, since the AppContainer still blocks his files, keyring and loopback; any edit moves them to the container automatically.

1. **Which burst provider to try first.** Ruling 74 answered "Contabo first; every other provider addable later", and onboarding from a provider's published instructions is now designed (AD-30). Ruling 76 makes burst matter (about 4 sessions on Contabo). Nothing is paid for yet. Recommend: add his Contabo box as an Amp runner (free) for `host_harness` trials and Cloudroom's free tier as a comparison, both through the onboarding flow; keep E2B, Modal and Cloudflare as adapters with no account; decide on cost per agent-hour after one measured week.
2. **Is `host_harness` acceptable at all** (a provider's harness holding the loop, transcript and run pass inside its VM, for compute only)? Ruling 75 gave no answer on provider-hosted harnesses. Recommend: yes, as a leaf node attempt with key accounts only, never owning schedules or state; refuse it if he wants every transcript on his own machines.
3. **Plan logins on Contabo and on an owned Amp runner.** Recommend: yes on both (his machines, signed in once by him through the CLI); never on a provider VM; the server's runners still default to key providers.
4. **What counts as an irreversible external effect** (the only steps that may wait for the inbox; ruling 77 says these are rare). Recommend: messages, posts, webhooks, outbound calls to non-QMX systems, desktop actions that submit or send, and app operations an app marks so; model spend, Library writes and file changes never count.

## Closed by rulings 73-88 (kept for the record)

- **Server specs** (old 4): answered by ruling 76: Contabo has 6 cores, 12 GB RAM and a 200 GB SSD, with an upgrade possible in December. `max_sessions` is derived from RAM after the colocated services (about 4 today, AD-30). Only a check remains, not a decision: `ls /dev/kvm` (a Windows VM for MT5/cTrader only if it exists) and the measured RAM of one session.
- **Default self-improvement rule** (old 6): answered by ruling 79 ("ship a default"): `self_improve: auto` for workflows he created or enabled, `propose_only` for templates he has not touched; `main` moves only by his click.
- **Hosting start** (part of old 1): answered by ruling 74: Contabo first.
- **Central relay or a relay per host:** answered by ruling 75 and designed in AD-28: the PC and Contabo keep their own relays, Contabo's is the central relay, and every other placement routes to it over Tailscale.
- **Inbox volume and notifications:** answered by ruling 77: the inbox is for provider failures and harness-level errors only (AD-17); notifications are designed by the UI session.
- **Creation and publishing:** answered by ruling 80: creation is human-driven first; drafts never live on `main`; run-made workflows, apps, pods and skills land as drafts; publishing asks him once (AD-11, AD-22).

Answered earlier and folded in: E1 engine seat, E2 real-model tests, E4 catch-up, Hermes scheduling, nothing waits (57), Library on his server (56, Library AD-19), plain servers first (55), the harness outside the sandbox (Rivet), credentials once everywhere (61), mixed providers (62, 63), Contabo as the always-on home (66, 69), one QMB machine (68), machines via provider dashboards (65, 67), Cua as a pack (60), chunking, compaction, caching and hooks (78, AD-34).
