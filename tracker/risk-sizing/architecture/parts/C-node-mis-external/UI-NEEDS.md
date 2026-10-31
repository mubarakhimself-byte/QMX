# UI needs from Part C

Design intent and screen proposals for the UI session. No UI code is written or edited (STATE midday ruling 45: "You're not going to touch my designs."). These build on what mini apps were designed to show: an app page with Operations and Setup tabs (`tracker/qma-v2/research/methodology/23-ui-shots`, as the experience pass read them, `funnel/experience/ui-needs.md` §8), and fold into existing views wherever they can. The words follow `funnel/experience/ui-needs.md` §0.

His words: "is it going to start as server, then show me that the server has started?" (T3:1102); "A server can be a server." (T3:1102); "the trading node is perhaps a firm" (T3:903).

## 1. Words on his screens

- A node's state: Setting up, Starting, Ready, Trading, Healing, Paused, Stopped by a risk rule, Stopped by a health check, Unreachable since `<time>`. One word, one line of reason, the detail one click away.
- "Trading node" names the app that trades. "Connect a server" names the QMX server setup that runs workflows and the Library. The two never share a word (OP-07).
- Machines are "This PC" and the name he gave a server. No machine kinds.
- Every figure shows its world: paper, demo or live (OP-08).
- A market that is shut says until when, from its calendar ("Shut until Sunday 22:00 your time") (OP-09).

## 2. The trading node page

The mini-app page as designed, with these tabs:

| Tab | Shows | Backend |
| --- | --- | --- |
| Overview | the state word and reason in large type; where it runs; its local time beside his; clock offset and band as a dot; each venue's session; units summary; kill level; "Pause all", "Kill switch" (levels), "Update", "Roll back"; the broker's own app named as the last way to close everything | `status` |
| Units | each deployment: world, account, markets, state per market (trading, warming up 140 of 200 bars, paused by you, stopped by a risk rule, stopped by a health check, market shut until), last trade, today's result in R; buttons pause, resume (his), withdraw | `units` |
| Positions | each position with its stop shown at the broker and when it was last seen there; untagged positions flagged "not ours, protected" | `positions` |
| Readings | this node's markets and the readings computed here and by the MIS beside it, each with its freshness word; a badge when a unit used a fallback | node `status`, `mis` `status`, reading history |
| Heals | every restart it made by itself: what, why, when (his time and node time), how many today; when healing keeps failing, the item it raised | node journal |
| Deploys | every deploy, withdraw, update and rollback: what, when, whose click, from which PC, applied or "waiting for London-1" | `deployments`, the node link's outbox |
| Checks and passport | the self-test lines with their last result; round trip to each venue; grant and agent-wallet expiry dates | `passport` |
| Logs | the node's logs, with a link to this machine's deep logs | the log shipper, OpenObserve |
| Operations, Setup | as the mini-app page designs them | the manifest |

**Cards that need his click** (the inbox's urgent level when trades are open):

- **Stop card**: what stopped, when (his time, UTC, node), which rule and its values, what happened to open trades (kept with broker stops, or closed), risk rule or health check, what it takes to resume; Resume (his), Back to paper, Retire.
- **Change card** (a broker changed a symbol): the old and new facts side by side, the checker's rerun, the units paused; Accept, Keep paused.
- **Identity card**: "This node's disk moved or was copied." Two buttons: "This is the same node, moved" and "Take over a dead node" (asks him to confirm the old one is gone; shows its last heartbeat).
- **Twin alarm**: "Another copy of this node may be trading this account." Entries stopped; what to check.
- **Soak cards** on a release and on a live binding: time done against 24 hours on This PC and one week on demo; shown, never blocking; his click decides.

## 3. Starting a node

- **This PC**: one button on Home's getting-started panel and on the Apps page. A list of steps that tick: checking this PC (clock, disk), waiting for cTrader to approve your app (with the link and what to paste), installing, your signature for this node version, signing in on cTrader's page, measuring the round trip, self-test with a small demo trade and its stop, ready. A note up front: "Runs while this PC is on. For round-the-clock trading, add a server."
- **A server**: the connect dialog's card-then-steps pattern with the trading node kind; the keys window on the server for the Hyperliquid agent wallet; the same step list. A failed step shows one line and two buttons: "Run this step again", "Help". Running the setup again picks up where it stopped.
- **Binding a live account**: a separate, deliberate flow on the node page: it turns off chats and agent steps on that server first, says so in one line, then the bind, then the soak card.

## 4. The deploy dialog

From a unit ("Deploy") or a node ("Add unit"): pick a node (Ready only), an account, markets (from his admitted list), lane (paper by default). A preflight list runs by itself and explains each red line in one sentence: same fingerprint as tested; this node's versions match; warm-up history available; a record for each market at this broker; minimum lot fits; clock fine; each reading the unit reads available or with a fallback; placeholders on a live account need his tick; two units on one symbol of a netting account. Then: accepted, compiling, warming up, trading. "Withdraw" stays one click away.

## 5. Several nodes, one clock

- A nodes strip on Home and in Portfolio's header: one tile per node (name, This PC or the server's name, state word, local time, clock dot, units, last heartbeat age).
- A world clock strip: his time first, each node's local time with its name, market sessions as bands drawn in each market's own zone (they shift through daylight saving by themselves), crypto all day.
- A notice a week before a zone mismatch week ("London and New York are 4 hours apart from 25 Oct to 1 Nov").
- An unreachable node greys out with "unreachable since 03:12 (your time)" and its last values; its account's positions still show from the PC's view-only broker read, labelled "read from the broker".

## 6. The MIS on his PC

Portfolio's MIS tab as designed (Live and Shadow switches, a since time, a value), plus: per reading its version, clock, markets, freshness word and which units read it with which fallback; a history chart with its state changes; "default" on readings his models will replace; a shadow model's record beside the default; his yes to make a shadow reading live. His question, "should it have some sort of like its own section in the QMN mini app?" (log 2026-10-31T10:43), is answered by both: the Readings tab on each node and this tab on his PC, one data.

## 7. Settings

| Area | Adds |
| --- | --- |
| Clocks (small, new) | display zone; each machine's offset and sync state; a button to turn on this PC's time sync (his click) |
| Keys | where each venue key lives ("lives on: London-1"); expiry dates; "Rotate" |
| Alarms | the ntfy topic and the Healthchecks.io check, a "send a test" button, the short wake list (editable) |
| Machines | nodes as their server's place with a trading node mark, This PC first, each with its clock health |
| Connections | CCXT rows that read perps; Hyperliquid with testnet; a paid futures data route as a row he adds later, with its monthly cost shown as a reading, never a cap |

## 8. Backend each screen needs

Every screen above reads the node link's latest values and the node and MIS operations in `CONTRACTS.md` §2 and §8; the setup flow reads the connect dialog's job progress (built); the clock strip reads heartbeat clock facts (slice C-01); the readings views read reading history (slice C-08 onward). Nothing here needs a new backend door beyond those.
