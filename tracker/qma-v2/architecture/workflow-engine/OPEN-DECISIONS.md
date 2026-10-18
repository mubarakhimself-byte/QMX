# Open decisions (what is still his; the design proceeds on the recommendation)

Refreshed 2026-10-16 night against rulings 73-88 (27c gap fixes). The three calls at the top are his; everything below them is either still open with a recommendation, or closed with the ruling that closed it.

## After the first build run (2026-10-18)

The calls A, B and C below are closed: A by ruling 89 (H0, H15, H16, H17 granted and built as HG1), B by ruling 90 (every account carries its own configurable background share; 50 % is only a default), C by ruling 91 (data is held until a deeper data study). The amendment after the run (`methodology/35`) adds these:

D. **Grant the HG3 harness round** (HARNESS-REQUESTS H2 re-asked, H18-H25, plus five harness bug fixes). **Recommend: yes, H2 first.** H2 is the one with a security reason: until an engine agent chat can be started without the built-in `Bash`, `Write`, `Edit` and `NotebookEdit`, agent nodes on the PC depend on an ask the engine rejects (AD-24, live check E35), and are held if that ask does not come. The rest are tidiness and cost (closing chats, a cached brief, no asks for draft saves, typing, a public `ControlService`, telling his clicks from the copilot's calls, chat routes for the engine host).

E. **Accept that edited workflows need Docker Desktop running** (AD-24). Only scripts byte-identical to what QMX shipped may run on the PC directly, and even those run inside a Windows AppContainer that cannot see his plan login, his keyring or QMX itself. A template he or the copilot edited runs its scripts in a container, so with Docker off it waits with "Docker is off" instead of running. **Recommend: yes.** Ruled the other way: edited scripts would run on the host inside the AppContainer too, which trusts the AppContainer alone for code nobody reviewed.

F. **Accept a money scan that fails closed with no allow-list** (AD-36). It reads every script, prompt, name and note for call-shaped money verbs with the harness gate's own matcher. It will sometimes refuse an innocent sentence ("write the order of the sections" reads as "write order"), and the fix is to reword. **Recommend: yes.** Ruled the other way: a reviewed allow-list of phrases, which is one more thing a model could try to widen.

## Calls for him first (closed, kept for the record)

A. **Harness grants H0, H15, H16, H17** (HARNESS-REQUESTS). H0 exports `Background` and `Child` from `qma/harness/__init__.py`; H17 adds `AGENT_OPERATIONS` table rows for the new engine, Library and Lab tools (draft save and test run are `DOMAIN_WRITE`, so they never ask; publish, enable and live runs are `MANAGE`, so they ask once); H15 is a per-chat compaction threshold and H16 per-chat hooks for Background chats. None is inside ruling 39's load-balancer exception, so ruling 24 needs his explicit yes. **Recommend: yes to all four.** H0 and H17 are export-only and table-row edits; H15 and H16 are what ruling 78 calls critical. Each has a fallback with no harness edit (a narrow import allow-list; draft saves through `library_save` plus a test-on-save watcher; an engine-driven compaction restart; tool spans read from session blocks), so a "no" slows the build but does not block it.

B. **Does the harness's 50 % plan background cap still apply to workflow agent nodes, given ruling 27** (no spending caps, no asking about usage)? Today a Background chat on the plan is refused at 50 % of the window (`QH/launch.py:182-188`). **Recommend: keep it for plan accounts only**, so his own copilot always has half the plan; key-provider accounts have no such cap, and the engine's admission control waits quietly at the cap instead of asking (SOLUTION-DESIGN §7.4). Ruled the other way: workflows may use the whole plan window, and his copilot can find it empty.

C. **Accept study 30 for the first data packets** (rulings 58, 81: data is among the first things built; tick backup and import are early work). No architecture owns the market-data service, the tick backup or the import of the orphaned ~10 GB history; study 30 §4-§5 designs them. **Recommend: accept study 30 §4-§5 as the binding design for the first data packets** (back up the 10 GB first, one ingest path, `qmx-marketdata` on Contabo, `dataset` cards in the Library) and schedule them first. Ruled the other way: a short spine pass on data runs before any data packet.

## Still open (the design proceeds on the recommendation)

0. **Whether the two templates that read the network (DB's calendar, T4's central-bank feeds) keep running `host_confined` with `network: true`, or move to the container tier** (AD-24). Recommend: keep them `host_confined` while they are byte-identical to the shipped pack, since the AppContainer still blocks his files, keyring and loopback; any edit moves them to the container automatically.

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
