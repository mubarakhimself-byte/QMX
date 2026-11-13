// His things, for every widget and page: units, proposals, sessions, runs,
// workflows, nodes. Also the page layout per kind (his Lego on pages) and
// the demo's decisions (promote, not yet, pause, retry, approve), so a click
// on a page shows at once in every widget that lists the same thing.
import { shell } from "./state.svelte";
import { objects, guests, worstGuests, guestSections, type Obj, type Kind, type Market, type Life } from "./model";

// Default page sections per kind, in order. He can reorder, hide and add;
// the layout applies to every thing of that kind.
const defaults: Partial<Record<Kind, string[]>> = {
  unit: ["results", "numbers", "journal", "where", "position", "proof", "used"],
};

function createThings() {
  // Each list remembers where he was.
  const scroll = $state<Record<string, number>>({});

  // Lego on pages.
  const layout = $state<Partial<Record<Kind, string[]>>>({});
  let editing = $state(false);

  // Demo decisions.
  const decided = $state<Record<string, "promoted" | "later">>({});
  const markets = $state<Record<string, Market[]>>({});
  const flows = $state<Record<string, "running" | "passed">>({});
  let approval = $state<"open" | "allowed" | "rejected">("open");

  const all = $derived.by((): Obj[] =>
    objects(shell.fixture).map((o) => {
      let x = o;
      if (markets[o.id]) x = { ...x, markets: markets[o.id] };
      if (x.kind === "unit" && x.markets) {
        const top = x.markets.some((m) => m.life === "live") ? "live" : x.markets.some((m) => m.life === "paper") ? "paper" : x.markets[0].life;
        const paused = x.markets.some((m) => m.paused);
        x = { ...x, word: paused ? "paused" : top, tone: paused ? "paper" : top === "live" ? "live" : top === "paper" ? "paper" : top === "retired" || top === "stopped" ? "down" : "idle" };
      }
      if (decided[o.id]) x = { ...x, needs: false, word: decided[o.id] === "promoted" ? "promoted" : "later", tone: decided[o.id] === "promoted" ? "up" : "idle" };
      if (flows[o.id]) x = { ...x, needs: false, word: flows[o.id], tone: flows[o.id] === "running" ? "run" : "up", line: flows[o.id] === "running" ? "Retrying from step 4" : "Passed on retry" };
      if (o.id === "a-ticks" && approval !== "open") x = { ...x, needs: false, word: approval, tone: approval === "allowed" ? "up" : "idle" };
      if (o.id === "r-helper2" && approval !== "open") x = { ...x, word: "done", tone: "up", line: approval === "allowed" ? "Downloaded and rebuilt EURUSD H1" : "Used data up to Dec 2023" };
      return x;
    }),
  );
  const byId = $derived(new Map(all.map((o) => [o.id, o])));

  return {
    get fixture() {
      return shell.fixture;
    },
    get all() {
      return all;
    },
    get(id: string) {
      return byId.get(id);
    },
    get needs() {
      return all.filter((o) => o.needs);
    },
    get running() {
      return all.filter((o) => o.kind === "run" && o.word === "running");
    },
    get guests() {
      if (shell.fixture === "first") return [];
      return shell.fixture === "worst" ? [...guests, ...worstGuests] : guests;
    },
    guest(id: string) {
      return [...guests, ...worstGuests].find((g) => g.id === id);
    },
    scrollOf: (k: string) => scroll[k] ?? 0,
    keepScroll(k: string, y: number) {
      scroll[k] = y;
    },
    say(text: string, undo?: () => void) {
      shell.say(text, undo);
    },

    // ----- pages (Lego)
    get editing() {
      return editing;
    },
    setEditing(on: boolean) {
      editing = on;
    },
    sectionsOf(o: Obj) {
      const own = o.sections ?? [];
      const order = layout[o.kind] ?? defaults[o.kind] ?? own.map((s) => s.id);
      const pool = [...own, ...guestSections.filter((g) => g.kind === o.kind)];
      // A unit's "Where it runs" follows its markets, so a promotion shows at once.
      const where = (m: Market) => {
        const n = m.node ? byId.get(m.node) : undefined;
        return n ? `${n.name} · ${n.where}${m.paused ? " · paused" : ""}` : "Not placed";
      };
      return order
        .map((id) => pool.find((s) => s.id === id))
        .filter((s) => !!s)
        .map((s) => (s.id === "where" && o.kind === "unit" && o.markets ? { ...s, body: { t: "facts" as const, facts: [...o.markets.map((m): [string, string] => [m.sym, where(m)]), ["Backtests", "This PC"] as [string, string]] } } : s));
    },
    // Sections this kind can show that are not on the page now.
    spareOf(o: Obj) {
      const on = new Set(this.sectionsOf(o).map((s) => s.id));
      return [...(o.sections ?? []), ...guestSections.filter((g) => g.kind === o.kind)].filter((s) => !on.has(s.id));
    },
    moveSection(o: Obj, id: string, d: -1 | 1) {
      const order = this.sectionsOf(o).map((s) => s.id);
      const i = order.indexOf(id);
      const j = i + d;
      if (i < 0 || j < 0 || j >= order.length) return;
      [order[i], order[j]] = [order[j], order[i]];
      layout[o.kind] = order;
    },
    removeSection(o: Obj, id: string) {
      layout[o.kind] = this.sectionsOf(o).map((s) => s.id).filter((x) => x !== id);
    },
    addSection(o: Obj, id: string) {
      layout[o.kind] = [...this.sectionsOf(o).map((s) => s.id), id];
    },
    resetSections(o: Obj) {
      delete layout[o.kind];
    },

    // ----- the demo's decisions
    decision: (id: string) => decided[id],
    promote(p: Obj) {
      const ev = p.evidence;
      if (!ev) return;
      decided[p.id] = "promoted";
      const u = byId.get(ev.unit);
      if (u?.markets) markets[u.id] = u.markets.map((m) => (m.sym === ev.sym ? { ...m, life: ev.to, target: undefined, node: ev.to === "paper" ? "n-home" : "n-fra" } : m));
      shell.say(`${u?.name ?? "Unit"} is on ${ev.to} on ${ev.sym}`, () => {
        delete decided[p.id];
        if (u) delete markets[u.id];
      });
    },
    later(p: Obj, why: string) {
      decided[p.id] = "later";
      shell.say(`Not yet: ${why.toLowerCase()}`, () => delete decided[p.id]);
    },
    setLife(u: Obj, sym: string, life: Life | "pause" | "resume") {
      const ms = (u.markets ?? []).map((m) =>
        m.sym !== sym ? m : life === "pause" ? { ...m, paused: true } : life === "resume" ? { ...m, paused: false } : { ...m, life, paused: false, node: life === "paper" ? "n-home" : life === "retired" ? undefined : m.node },
      );
      const before = u.markets;
      markets[u.id] = ms;
      const word = life === "pause" ? "paused: no new trades" : life === "resume" ? "trading again" : `now ${life}`;
      shell.say(`${sym} ${word}`, () => before && (markets[u.id] = before));
    },
    flow: (id: string) => flows[id],
    retry(w: Obj) {
      flows[w.id] = "running";
      shell.say(`${w.name}: retrying from step 4`);
      setTimeout(() => (flows[w.id] = "passed"), 2600);
    },
    get approval() {
      return approval;
    },
    answer(a: "allowed" | "rejected") {
      approval = a;
    },
  };
}

export const things = createThings();

