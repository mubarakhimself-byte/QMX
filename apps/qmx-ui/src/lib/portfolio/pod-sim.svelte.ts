/**
 * What you can do to a Portfolio pod in the browser (demo): pick how it
 * sizes risk, move its knobs, ladder and bot weights as a draft, save the
 * draft as the next version, pause and resume it, and look at its live or
 * paper side. Every figure the pod screens show is derived here, so a change
 * moves the numbers on every panel at once.
 */
import {
  deepestDip,
  growth,
  ladderMult,
  replay,
  type Step,
} from "$lib/demo/sizing-math";
import { PODS, type Method, type Pod } from "./demo";

export type MethodKind = Method["kind"];

/** Sizing methods and how each leans on wins and losses in the demo replay. */
export const METHODS: {
  kind: MethodKind;
  label: string;
  gain: number;
  loss: number;
}[] = [
  { kind: "book", label: "Book + BMS", gain: 1, loss: 1 },
  { kind: "model", label: "Model", gain: 0.9, loss: 0.75 },
  { kind: "workflow", label: "Workflow", gain: 0.95, loss: 0.9 },
  { kind: "hybrid", label: "Hybrid", gain: 0.85, loss: 0.7 },
  { kind: "rules", label: "Simple rules", gain: 1, loss: 1.05 },
];
export const methodOf = (k: MethodKind) => METHODS.find((m) => m.kind === k)!;

export type Settings = {
  method: MethodKind;
  knobs: Record<string, number>;
  weights: Record<string, number>;
  ladder: Step[];
};

const DOCS_LADDER: Step[] = [
  { at: 5, mult: 0.5 },
  { at: 10, mult: 0.25 },
];

function defaults(p: Pod): Settings {
  return {
    method: p.method.kind,
    knobs: Object.fromEntries(p.knobs.map((k) => [k.key, k.value])),
    weights: Object.fromEntries(p.bots.map((b) => [b.id, b.weight])),
    ladder: p.method.kind === "book" ? DOCS_LADDER : [],
  };
}
const clone = (s: Settings): Settings => JSON.parse(JSON.stringify(s));
const same = (a: Settings, b: Settings) =>
  JSON.stringify(a) === JSON.stringify(b);

/** Risk relative to the pod's own defaults, from the knobs that set it. */
function riskScale(p: Pod, s: Settings): number {
  let m = 1;
  for (const k of p.knobs) {
    const v = s.knobs[k.key];
    if (k.key === "risk" || k.key === "target") m *= v / k.value;
    if (k.key === "leverage") m *= Math.sqrt(v / k.value);
  }
  return m;
}

export type Side = "live" | "paper";

export type PodView = {
  pod: Pod;
  side: Side;
  hasLive: boolean;
  paused: boolean;
  version: string;
  equity: number;
  today: number;
  curve: number[];
  /** The other side's curve, for the dashed line. */
  other: number[] | null;
  floor: number;
  room: number;
  /** Room left as a share of start minus kill line. */
  roomShare: number;
  method: MethodKind;
  /** Money at stake on the next trade, after the ladder. */
  perTrade: number;
  /** Losing trades in a row before the kill line. */
  tradesToKill: number;
  dailyStop: number | null;
  dip: number;
  /** Rows for "Limits right now". */
  limits: { name: string; now: string; limit: string; used: number }[];
};

export type DraftView = {
  version: string;
  changes: string[];
  curve: number[];
  gain: number;
  dip: number;
  stoodDown: boolean;
};

const usd = (n: number) =>
  `$${Math.round(Math.abs(n)).toLocaleString("en-US")}`;

class PodSim {
  saved = $state<Record<string, Settings>>({});
  drafts = $state<Record<string, Settings>>({});
  paused = $state<Record<string, boolean>>({});
  sides = $state<Record<string, Side>>({});
  bumps = $state<Record<string, number>>({});

  private pod(id: string) {
    return PODS.find((p) => p.id === id)!;
  }
  settings(id: string): Settings {
    return this.saved[id] ?? defaults(this.pod(id));
  }
  draft(id: string): Settings {
    return this.drafts[id] ?? this.settings(id);
  }
  isDirty(id: string) {
    return !!this.drafts[id] && !same(this.drafts[id], this.settings(id));
  }
  edit(id: string, change: (s: Settings) => void) {
    const next = clone(this.draft(id));
    change(next);
    this.drafts[id] = next;
  }
  discard(id: string) {
    delete this.drafts[id];
  }
  /** Save the draft as the next version. Returns the new version label. */
  save(id: string) {
    if (!this.drafts[id]) return this.versionOf(id);
    this.saved[id] = this.drafts[id];
    delete this.drafts[id];
    this.bumps[id] = (this.bumps[id] ?? 0) + 1;
    return this.versionOf(id);
  }
  versionOf(id: string, ahead = 0) {
    const p = this.pod(id);
    const n = +(p.version.match(/\d+/)?.[0] ?? 1) + (this.bumps[id] ?? 0);
    return `v${n + ahead}`;
  }
  togglePause(id: string) {
    this.paused[id] = !this.paused[id];
  }
  side(id: string): Side {
    const p = this.pod(id);
    return p.mode === "LIVE" ? (this.sides[id] ?? "live") : "paper";
  }
  setSide(id: string, s: Side) {
    this.sides[id] = s;
  }

  /** The pod on the side being looked at, with any draft applied to its figures. */
  view(id: string): PodView {
    const p = this.pod(id);
    const s = this.draft(id);
    const side = this.side(id);
    const hasLive = p.mode === "LIVE";
    const paused = !!this.paused[id];
    const base =
      side === "live"
        ? { equity: p.equity, today: p.today, curve: p.curve }
        : p.paper;
    const floor = s.knobs.floor ?? p.floor;
    const room = base.equity - floor;
    const dipNow =
      ((Math.max(...base.curve) - base.curve[base.curve.length - 1]) /
        Math.max(...base.curve)) *
      100;
    const riskPct = s.knobs.risk ?? 0.5 * riskScale(p, s);
    const perTrade = paused
      ? 0
      : ((base.equity * riskPct) / 100) * ladderMult(dipNow, s.ladder);
    const dailyStop =
      s.knobs.daily !== undefined ? (base.equity * s.knobs.daily) / 100 : null;
    const limits: PodView["limits"] = [
      {
        name: "Room to kill line",
        now: usd(room),
        limit: `line ${usd(floor)}`,
        used: Math.max(0, Math.min(1, 1 - room / (p.start - floor))),
      },
    ];
    for (const g of p.guards) {
      if (g.name === "Above kill line") continue;
      if (g.name === "Daily loss" && dailyStop !== null) {
        const now = +g.now.replace(/[^\d.]/g, "");
        limits.push({
          name: g.name,
          now: g.now,
          limit: `of ${usd(dailyStop)}`,
          used: Math.min(1, now / dailyStop),
        });
      } else limits.push({ ...g, limit: `of ${g.limit}` });
    }
    return {
      pod: p,
      side,
      hasLive,
      paused,
      version: this.versionOf(id),
      equity: base.equity,
      today: paused ? 0 : base.today,
      curve: base.curve,
      other: side === "live" ? p.paper.curve : hasLive ? p.curve : null,
      floor,
      room,
      roomShare: Math.max(0, room / (p.start - floor)),
      method: s.method,
      perTrade,
      tradesToKill: perTrade > 0 ? Math.floor(room / perTrade) : Infinity,
      dailyStop,
      dip: deepestDip(base.curve),
      limits,
    };
  }

  /** The same history replayed with the draft, or null when nothing changed. */
  preview(id: string): DraftView | null {
    if (!this.isDirty(id)) return null;
    const p = this.pod(id);
    const from = this.settings(id);
    const to = this.draft(id);
    const v = this.view(id);
    const a = methodOf(from.method);
    const b = methodOf(to.method);
    const out = replay(v.curve, {
      made: from.ladder,
      scale: riskScale(p, to) / riskScale(p, from),
      gain: b.gain / a.gain,
      loss: b.loss / a.loss,
      ladder: to.ladder,
      killAt: ((p.start - (to.knobs.floor ?? p.floor)) / p.start) * 100,
    });
    const changes: string[] = [];
    if (from.method !== to.method)
      changes.push(`Method ${a.label} → ${b.label}`);
    for (const k of p.knobs)
      if (from.knobs[k.key] !== to.knobs[k.key])
        changes.push(
          `${k.label} ${fmtKnob(from.knobs[k.key], k.unit)} → ${fmtKnob(to.knobs[k.key], k.unit)}`,
        );
    for (const bot of p.bots)
      if (from.weights[bot.id] !== to.weights[bot.id])
        changes.push(
          `${bot.name} ${from.weights[bot.id]}% → ${to.weights[bot.id]}%`,
        );
    if (JSON.stringify(from.ladder) !== JSON.stringify(to.ladder))
      changes.push("Ladder steps");
    return {
      version: this.versionOf(id, 1),
      changes,
      curve: out.curve,
      gain: growth(out.curve),
      dip: deepestDip(out.curve),
      stoodDown: out.stoodDownAt !== null,
    };
  }
}

export const fmtKnob = (v: number, unit: string) =>
  unit === "$" ? usd(v) : `${v}${unit}`;

export const podSim = new PodSim();
