import { replaceState } from "$app/navigation";
import { places as demoPlaces, type Panel, type Place } from "./data";
import { objects, type ListKind } from "./model";
import { worst } from "./worst";

export type Look = "night" | "terminal";
export type Fixture = "demo" | "worst" | "first";
export type DetailTab = { id: string; place: string; panel: Panel };
// A page one level (or more) under a place: a thing, or one of its sections
// on its own. `list` is the list it was opened from, shown as a narrow spine
// beside the page so he keeps his place.
export type At = { id: string; sub?: string; list?: ListKind };

const param = (k: string, fallback: string) =>
  typeof location === "undefined" ? fallback : (new URLSearchParams(location.search).get(k) ?? fallback);

const enc = (a: At) => `${a.id}${a.sub ? `/${a.sub}` : ""}${a.list ? `@${a.list}` : ""}`;
function dec(s: string): At {
  const [path, list] = s.split("@");
  const [id, sub] = path.split("/");
  return { id, sub: sub || undefined, list: (list || undefined) as ListKind | undefined };
}

// Demo only: widgets that received something since you last looked.
const fresh = new Set(["overview:waiting", "overview:since", "trading:positions", "trading:t:u-gold"]);

function createShell() {
  const f0 = param("data", "demo");
  let fixture = $state<Fixture>((["demo", "worst", "first"].includes(f0) ? f0 : "demo") as Fixture);
  const p0 = param("place", "overview");
  let place = $state(demoPlaces.some((p) => p.id === p0) || p0.startsWith("app:") ? p0 : "overview");
  const at0 = param("at", "");
  let stack = $state<At[]>(at0 && fixture !== "first" && objects(fixture).some((o) => o.id === dec(at0).id) ? [dec(at0)] : []);
  let look = $state<Look>(param("look", "night") === "terminal" ? "terminal" : "night");
  let text = $state(param("text", "standard"));
  let details = $state<DetailTab[]>([]);
  let detail = $state<string | null>(null);
  let dock = $state(false);
  let sent = $state<string[]>([]);
  let toast = $state<{ text: string; undo?: () => void } | null>(null);
  let toastTimer: ReturnType<typeof setTimeout> | undefined;

  const sync = () => {
    if (typeof history === "undefined") return;
    const url = new URL(location.href);
    url.searchParams.set("place", place);
    const top = stack[stack.length - 1];
    if (top) url.searchParams.set("at", enc(top));
    else url.searchParams.delete("at");
    url.searchParams.set("data", fixture);
    url.searchParams.set("text", text);
    url.searchParams.delete("nav");
    if (look !== "night") url.searchParams.set("look", look);
    else url.searchParams.delete("look");
    try {
      replaceState(url, {}); // SvelteKit's own, so its router stays in step
    } catch {
      history.replaceState(history.state, "", url); // before the router starts
    }
  };

  const allPlaces = $derived(fixture === "worst" ? worst(demoPlaces) : demoPlaces);

  return {
    get places(): Place[] {
      return allPlaces;
    },
    get place() {
      return place;
    },
    // Where he is. A mini app is a place of its own while it is open.
    get current(): Place {
      if (place.startsWith("app:")) {
        return { id: place, name: "Mini app", icon: "puzzle", kind: "app", purpose: "", board: [], first: { title: "", line: "", action: "", steps: [] } };
      }
      return allPlaces.find((p) => p.id === place) ?? allPlaces[0];
    },
    get look() {
      return look;
    },
    get fixture() {
      return fixture;
    },
    get text() {
      return text;
    },
    get details() {
      return details;
    },
    get detail() {
      return detail;
    },
    get activeDetail() {
      return details.find((d) => d.id === detail) ?? null;
    },
    get dock() {
      return dock;
    },
    get sent() {
      return sent;
    },

    // ----- the trail: a place, then the pages opened from it
    get stack() {
      return stack;
    },
    get page(): At | undefined {
      return stack[stack.length - 1];
    },
    // Opening something from where he is adds to the trail.
    open(a: At) {
      const top = stack[stack.length - 1];
      if (top && enc(top) === enc(a)) return;
      // A sibling picked in the list spine replaces the page, so Back still goes to the list.
      if (top && a.list && top.list === a.list && !top.sub && !a.sub) stack[stack.length - 1] = a;
      else stack.push(a);
      sync();
    },
    // Back: one page up the trail, then out of a widget's own tab.
    back() {
      if (stack.length) stack.pop();
      else if (detail) detail = null;
      sync();
    },
    // Back to step i of the trail (-1 is the place itself).
    jump(i: number) {
      stack = stack.slice(0, i + 1);
      if (i < 0) detail = null;
      sync();
    },
    get canBack() {
      return stack.length > 0 || !!detail;
    },

    hasNew: (id: string) => fixture !== "first" && fresh.has(`${place}:${id}`),
    // A navigation click starts a fresh trail.
    go(id: string) {
      place = id;
      stack = [];
      detail = null;
      sync();
    },
    setLook(l: Look) {
      look = l;
      sync();
    },
    setFixture(f: Fixture) {
      fixture = f;
      if (f === "first") stack = [];
      else stack = stack.filter((a) => objects(f).some((o) => o.id === a.id));
      sync();
    },
    setText(t: string) {
      text = t;
      document.documentElement.dataset.text = t;
      sync();
    },
    // Expand: a widget opens as its own tab, one level deeper.
    expand(panel: Panel) {
      const id = `${place}:${panel.id}`;
      if (!details.some((d) => d.id === id)) details.push({ id, place, panel });
      detail = id;
      stack = [];
      sync();
    },
    openDetail(id: string) {
      const d = details.find((x) => x.id === id);
      if (!d) return;
      place = d.place;
      detail = id;
      stack = [];
      sync();
    },
    closeDetail(id: string) {
      details = details.filter((d) => d.id !== id);
      if (detail === id) detail = null;
    },
    toggleDock(open?: boolean) {
      dock = open ?? !dock;
    },
    // Hand a widget or a thing to the copilot: it lands in the dock as context.
    send(title: string) {
      if (!sent.includes(title)) sent.push(title);
      dock = true;
    },
    unsend(title: string) {
      sent = sent.filter((s) => s !== title);
    },

    // ----- one line of feedback, with undo where it makes sense
    get toast() {
      return toast;
    },
    say(t: string, undo?: () => void) {
      clearTimeout(toastTimer);
      toast = { text: t, undo };
      toastTimer = setTimeout(() => (toast = null), 5000);
    },
    hush() {
      toast = null;
    },
  };
}

export const shell = createShell();
