import { PAGES, pill, chips, figCard, bars, flow, cards, table, figScript, head, panel, opts, was, ROUND1 } from "./site2.mjs";
import { envelopeFig } from "./fig-envelope.mjs";
import { routerFig } from "./fig-router.mjs";

export const CONTENT = {};
const page = (fn) => (p) => { const { body, script } = fn(p); return { body: body.join(""), script }; };
export { page };

// ---------------------------------------------------------------- envelope
const EB = {
  markets: [["EURUSD", true, true], ["GBPUSD", true], ["XAUUSD", true], ["NAS100"], ["BTCUSD"]],
  sessions: [["Asia"], ["London", true], ["New York", true]],
  brokers: [["IC cTrader", true], ["IC MT5"], ["Hyperliquid"]],
  offers: [["GBPUSD", "London", "IC cTrader"], ["XAUUSD", "New York", "IC cTrader"], ["NAS100", "London", "IC cTrader"], ["EURUSD", "Asia", "IC cTrader"], ["BTCUSD", "Asia", "Hyperliquid"]],
};
const tick = (group, [name, on, home]) => `<label${home ? ' class="home"' : ""}><input type="checkbox" id="eb-${group}-${name.replace(/\W/g, "")}" data-g="${group}" value="${name}"${on ? " checked" : ""}${home ? " disabled" : ""}>${name}${home ? " · home" : ""}</label>`;
const builder = `<div class="eb">
<fieldset><legend>Markets</legend><div class="ticks">${EB.markets.map((m) => tick("m", m)).join("")}</div></fieldset>
<fieldset><legend>Sessions</legend><div class="ticks">${EB.sessions.map((m) => tick("s", m)).join("")}</div></fieldset>
<fieldset><legend>Brokers</legend><div class="ticks">${EB.brokers.map((m) => tick("b", m)).join("")}</div></fieldset>
<div><p class="note" style="margin:0 0 6px">Now let the router send an offer:</p><div class="offers">${EB.offers.map(([m, s, b], i) => `<button type="button" data-o="${i}" aria-pressed="false"><span>${m} · ${s}</span><small>${b}</small></button>`).join("")}</div></div>
<div class="verdict" id="eb-verdict" aria-live="polite"><b>Pick an offer</b><p>Tick what your click covers, then tap an offer to see where it lands.</p></div></div>`;
const builderJs = `(()=>{const O=${JSON.stringify(EB.offers)};const v=document.getElementById("eb-verdict");let cur=-1;
const on=(g)=>[...document.querySelectorAll('input[data-g="'+g+'"]')].filter(i=>i.checked).map(i=>i.value);
function show(){if(cur<0)return;const [m,s,b]=O[cur];const miss=[];if(!on("m").includes(m))miss.push(m);if(!on("s").includes(s))miss.push(s+" session");if(!on("b").includes(b))miss.push(b);
if(!miss.length){v.dataset.v="in";v.innerHTML="<b>Inside the envelope: live advice</b><p>The unit takes it only if its own conditions hold right now. Taken or ignored, it is logged. No click needed: you already admitted "+m+", "+s+" and "+b+".</p>";}
else{v.dataset.v="out";v.innerHTML="<b>Outside the envelope: paper only</b><p>Not ticked: "+miss.join(", ")+". It never trades live. It becomes a paper sibling plus a proposal card. Only your click widens the envelope.</p>";}}
document.querySelectorAll(".offers button").forEach(b=>b.addEventListener("click",()=>{cur=+b.dataset.o;document.querySelectorAll(".offers button").forEach(x=>x.setAttribute("aria-pressed",String(x===b)));show();}));
document.querySelectorAll(".eb input").forEach(i=>i.addEventListener("change",show));})();`;

CONTENT["envelope.html"] = page((p) => {
  const f = envelopeFig();
  return { script: figScript("fig-env", f) + builderJs, body: [
    head(p, "proposed", "Your click admits a unit together with its markets, sessions and brokers. Inside that envelope the router only directs. Outside it, an offer becomes a paper sibling and a proposal for you."),
    figCard({ id: "fig-env", name: "Fig 1 · The fenced tray", svg: f.svg, modes: [["walk", "Walk through"], ["home", "Router off: a"], ["env", "Router off: b"], ["last", "Router off: c"]] }),
    chips("fig-env", [
      ["proposed", "<b>Your click</b> is the only thing that admits a unit to live", "lock"],
      ["proposed", "<b>Inside</b>: the router directs; the unit's own conditions decide", "envelope"],
      ["proposed", "<b>Outside</b>: never live; a paper sibling plus a proposal card", "paper"],
      ["proposed", "The <b>home market</b> is never the router's to give or take", "m0"],
      ["open", "The three 'Router off' buttons are the options of question 3", null],
    ]),
    `<h2>Why this one idea matters</h2><p>It makes three of your rulings fit together at once.</p>`,
    panel("", cards([
      { k: "Ruling", v: "The router directs, never switches", p: "Inside the envelope it only offers." },
      { k: "Ruling", v: "Only you promote", p: "Nothing outside your ticks trades live." },
      { k: "Ruling", v: "New market = sibling unit", p: "An offer outside becomes a paper sibling." },
    ])),
    `<h2>Try it</h2><p>Tick what your click covers. Then send offers.</p>`,
    panel("", builder),
    `<h2>What the envelope holds</h2>`,
    panel("", cards([
      { k: "Markets", v: "Broker · account · instrument", p: "e.g. IC cTrader, raw, GBPUSD." },
      { k: "Sessions", v: "Windows", p: "Asia, London, New York, overlaps." },
      { k: "Router mode", v: "Ignore · advise · follow", p: "Default: advise. Per unit, editable." },
      { k: "Router off", v: "Home · envelope · last offers", p: "What the unit does without it (question 3)." },
      { k: "Signed", v: "By you only", p: "With the date. Nothing else can write it." },
    ])),
    `<h2>Where it could live</h2>`,
    opts([
      ["i", "Inside the unit", "In the unit's own markets list, which the Library already has a tab for. A changed envelope is a new unit version."],
      ["ii", "A separate admission record", "Linked to the unit. Your click does not create a new version, and the store refuses any writer but you."],
    ]),
    `<h2>Round 1 → round 2</h2>`,
    was("A sibling of an admitted unit goes live at minimum lot without your click, paid from a monthly evidence budget.", "You rejected that. Nothing enters live without you. Outside the envelope means paper only, plus a proposal card."),
    chips("fig-env", [
      ["found", "The Library's unit kind has a <b>Markets</b> tab, with empty fields today", null],
      ["found", "The store already refuses writes from anyone who doesn't own the record", null],
      ["open", "<b>Question 2</b>: one market, an envelope you tick, or anything the unit's conditions allow", null],
    ]),
  ] };
});

// ---------------------------------------------------------------- router
CONTENT["router.html"] = page((p) => {
  const f = routerFig();
  return { script: figScript("fig-rt", { ...f, mode: "offers" }), body: [
    head(p, "proposed", "Like a load balancer: the market is the traffic, units are the servers. The router offers; units decide. It never switches a unit on or off."),
    figCard({ id: "fig-rt", name: "Fig 2 · Offers, not switches", svg: f.svg, modes: [["offers", "Offers"], ["p2", "Power of two"], ["cost", "Least cost"], ["affinity", "Affinity"], ["rr", "Round robin"], ["down", "Router down"]] }),
    chips("fig-rt", [
      ["proposed", "Its whole door can be one call: <b>offers now</b>, each with an expiry", "board"],
      ["proposed", "<b>Units pull</b> offers. Nothing ever waits on the router", "units"],
      ["proposed", "<b>Decision log</b>: offers issued with their inputs; units log taken or ignored", "log"],
      ["proposed", "<b>Correlation ledger</b>: units' results and signals, instruments, long/short consensus", "corr"],
      ["proposed", "Deletion test: remove the router and units lose only <b>extra traffic</b>", "board"],
    ]),
    `<h2>Round 1 → round 2</h2>`,
    was("A planner on the PC and a gate on the node that closes to new entries. After 5 trading days without a plan: no new entries anywhere.", "No gate: it was a switch. Its checks (spread, news, feed, session) move to the unit's own conditions and the guards. Offers expire; units keep trading what you admitted."),
    `<h2>Balancing algorithms, mapped</h2><p>The direction flips: an opportunity is the request, units are the servers. Use the buttons on the figure.</p>`,
    panel("", table(["Algorithm", "On the web", "In QMX", "Earns a place?"], [
      ["Power of two", "Pick 2, send to the less busy", "Pick 2 units, offer to the less correlated", '<span class="y">YES</span>'],
      ["Least cost", "Fastest server", "Cheapest broker and hour now, from the market journal", '<span class="y">YES</span>'],
      ["Affinity", "Same key, same server", "A unit keeps its markets; instruments sharded to nodes", '<span class="y">YES</span>'],
      ["Weighted", "More turns for strong servers", "More offers to units with stronger proof", '<span class="h">PART</span>'],
      ["Least connections", "Fewest open connections", "Market with the fewest look-alike units engaged", '<span class="h">PART</span>'],
      ["Round robin", "Next in turn", "Rotate to gather paper evidence", '<span class="n">PAPER</span>'],
      ["Random", "Uniform", "A share for exploring, paper only", '<span class="n">PAPER</span>'],
    ])),
    panel("A default hybrid (an option, editable)", flow([{ t: "Eligible", s: "envelope + conditions" }, { t: "Affinity first" }, { t: "Power of two", s: "by correlation" }, { t: "Weight", s: "by grade" }, { t: "Tie-break", s: "least cost" }]) + `<p class="note" style="margin-top:10px">Each stage is a named, versioned rule you can change in the UI.</p>`),
    `<h2>Three shapes for the router</h2>`,
    opts([
      ["A", "Advice board", "One central publisher; units pull their offers. Router down: offers expire, units trade their envelope. Keeps a central view of herding and of the router's own value."],
      ["B", "Round 1's planner, gate turned into a lookup", "Smallest change from what you read. The lookup answers advised, not advised or unknown. Risk: someone wires 'not advised' back into a block."],
      ["C", "Each unit chooses", "Units pick from a shared feed of market labels. Nothing central can fail, but there is no central view and the decision log scatters over 200 journals."],
    ]),
    `<h2>Who owns the correlation ledger</h2>`,
    panel("", table(["Owner", "Effect"], [
      ["Router", "Matches your words, but the pod must read the router to enforce same-bet limits: against independence"],
      ["Pod", "As the old BMS did. The router reads the pod, which is local and always on"],
      ["Shared, own writer", "A small job writes it; router reads for direction, pod for limits. Delete the router and the pod keeps its ledger"],
    ])),
    `<h2>One router or many</h2>`,
    panel("", cards([
      { k: "Shape 1", v: "One planner, slices", p: "Computes offers for all units; each node gets its slice." },
      { k: "Shape 2", v: "One per node", p: "Each node routes its own units; all read one correlation ledger." },
      { k: "Shape 3", v: "Edge + centre", p: "Fast offers per node, slow ones (new markets, siblings) from one planner." },
    ]) + `<p class="note" style="margin-top:10px">On the PC alone, all three collapse to one router. Adding a node moves only a slice of instruments.</p>`),
    `<h2>Market-label models per instrument</h2>`,
    panel("", flow([{ t: "Rules first", s: "spread, volatility, session" }, { t: "Pooled model", s: "per class, e.g. FX majors" }, { t: "Small per-instrument fit" }]) + `<p class="note" style="margin-top:10px">The PC trains; a server may stand in; the node never trains. Retrain on a frozen month, a decay alarm or your click, never on a timer nobody reads.</p>`),
    chips("fig-rt", [
      ["found", "The name <b>router</b> already belongs to the AI-model router in the code", null],
      ["open", "<b>Question 8</b>: a name for the trading router", null],
      ["open", "Questions 2, 3 and 4 shape what offers may do", null],
    ]),
  ] };
});

