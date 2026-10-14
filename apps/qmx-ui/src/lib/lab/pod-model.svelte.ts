/**
 * The Lab's pods as settings you can change (demo maths in the browser).
 * Each block in a pod's stack has parameters; Design edits them, and the
 * Size trail, Pod equity, Stress board, Drawdown fan and Head to head on
 * Test all read the result from here, so a change in Design shows in Test.
 * Paper runs can be paused, resumed, extended and stopped.
 */
import {
  deepestDip,
  growth,
  ladderMult,
  replay,
  type Step,
} from "$lib/demo/sizing-math";
import {
  FAN,
  LAB_PODS,
  PAPER_RUNS,
  POD_ATTRS,
  POD_EQUITY,
  STRESS_GRID,
  blockById,
  type LabPod,
  type SlotId,
  type StressCell,
} from "./pods";

export type Unit = "%" | "$" | "×" | "min" | "h" | "d" | "";
export type Param = {
  key: string;
  label: string;
  min: number;
  max: number;
  step: number;
  value: number;
  unit: Unit;
};

const p = (
  key: string,
  label: string,
  value: number,
  min: number,
  max: number,
  step: number,
  unit: Unit,
): Param => ({ key, label, value, min, max, step, unit });

/** What each block lets you set. Blocks missing here have nothing to set. */
export const PARAMS: Record<string, Param[]> = {
  "fixed-frac": [p("risk", "Risk to the stop", 0.5, 0.1, 2, 0.05, "%")],
  "fixed-usd": [p("usd", "Per trade", 100, 10, 2000, 10, "$")],
  "vol-target": [p("vol", "Daily move target", 1, 0.25, 3, 0.25, "%")],
  kelly: [
    p("frac", "Kelly fraction", 0.25, 0.05, 1, 0.05, "×"),
    p("cap", "Cap", 2, 0.5, 5, 0.25, "%"),
  ],
  "model-sizer": [p("ceiling", "Ceiling", 1, 0.25, 3, 0.25, "%")],
  parity: [p("window", "Look-back", 90, 30, 365, 15, "d")],
  tilt: [p("tilt", "Tilt", 50, 0, 100, 5, "%")],
  ladder: [
    p("at1", "Step 1 at", 5, 1, 30, 1, "%"),
    p("mult1", "Step 1 size", 0.5, 0, 1, 0.05, "×"),
    p("at2", "Step 2 at", 10, 1, 40, 1, "%"),
    p("mult2", "Step 2 size", 0.25, 0, 1, 0.05, "×"),
  ],
  regime: [
    p("chop", "In chop", 0.5, 0, 1, 0.05, "×"),
    p("crash", "In a crash", 0, 0, 1, 0.05, "×"),
  ],
  "vol-spike": [
    p("mult", "Size in a spike", 0.5, 0, 1, 0.05, "×"),
    p("hours", "For", 2, 0.5, 12, 0.5, "h"),
  ],
  "thin-hours": [p("mult", "Weekend size", 0.5, 0, 1, 0.05, "×")],
  streak: [p("losses", "Bench after losses", 4, 2, 10, 1, "")],
  cooldown: [p("min", "Wait after a loss", 30, 5, 240, 5, "min")],
  kill: [p("kill", "Below start", 20, 5, 40, 1, "%")],
  brakes: [p("daily", "Daily stop", 3, 0.5, 10, 0.5, "%")],
  "news-kill": [p("window", "Around news", 30, 5, 120, 5, "min")],
  caps: [
    p("coin", "Most in one coin", 25, 5, 100, 5, "%"),
    p("positions", "Open positions", 8, 1, 20, 1, ""),
  ],
  "corr-cap": [p("cluster", "Per cluster", 40, 10, 100, 5, "%")],
  "liq-cap": [p("liq", "Of 1h volume", 1, 0.1, 5, 0.1, "%")],
  "venue-cap": [
    p("venue", "On one exchange", 60, 10, 100, 5, "%"),
    p("stable", "In one stablecoin", 50, 10, 100, 5, "%"),
  ],
  "vol-input": [p("days", "Window", 30, 7, 90, 1, "d")],
};

/** Where a pod's defaults differ from a block's. */
const POD_DEFAULTS: Record<string, Record<string, Record<string, number>>> = {
  trend: { "fixed-frac": { risk: 0.75 }, kill: { kill: 15 } },
  voltarget: { kill: { kill: 12 } },
};

export function fmt(v: number, unit: Unit) {
  if (unit === "$") return `$${v.toLocaleString("en-US")}`;
  if (unit === "×") return `×${v}`;
  if (unit === "min") return `${v} min`;
  if (unit === "d") return `${v} days`;
  return `${v}${unit}`;
}

/** The sample trade the Size trail walks through the pod. */
export const SAMPLE = {
  bot: "BTC breakout",
  entry: 64150,
  stop: 63500,
  equity: 25000,
  lot: 0.00001,
  fee: 0.001,
};

type Values = Record<string, Record<string, number>>;

class PodModel {
  /** The sample trade's market: how far the pod is under its peak, and whether it is a weekend. */
  sample = $state({ dip: 6, weekend: true });
  /** Edited parameter values per pod, per block. */
  values = $state<Record<string, Values>>({});
  /** Blocks added or removed in Design, per pod (a draft until saved). */
  stacks = $state<Record<string, Record<SlotId, string[]>>>({});
  /** Saved versions bumped in this session. */
  bumps = $state<Record<string, number>>({});
  /** Stress cells you ran in the browser (pod → scenario → cell). */
  ran = $state<Record<string, Record<string, StressCell>>>({});
  /** Paper runs: paused, extra soak days, stopped. */
  paperPaused = $state<Record<string, boolean>>({});
  paperExtra = $state<Record<string, number>>({});
  paperStopped = $state<Record<string, boolean>>({});

  /** Pods sent to paper in this session. */
  stages = $state<Record<string, LabPod["stage"]>>({});
  stage(id: string): LabPod["stage"] {
    return this.stages[id] ?? this.pod(id).stage;
  }
  private sent = $state<Record<string, string>>({});
  /** True when the current version is already on paper (or live). */
  onPaper(id: string) {
    const was = ["paper", "live"].includes(this.pod(id).stage)
      ? this.pod(id).version
      : null;
    return (this.sent[id] ?? was) === this.version(id);
  }
  sendToPaper(id: string) {
    this.sent[id] = this.version(id);
    this.stages[id] = "paper";
  }

  pod(id: string): LabPod {
    return LAB_PODS.find((x) => x.id === id) ?? LAB_PODS[0];
  }
  /** `defaults` reads the pod as shipped, before any edit. */
  stack(id: string, defaults = false) {
    return (defaults ? undefined : this.stacks[id]) ?? this.pod(id).stack;
  }
  has(id: string, block: string, defaults = false) {
    return Object.values(this.stack(id, defaults)).some((l) =>
      l.includes(block),
    );
  }
  setStack(id: string, slot: SlotId, list: string[]) {
    this.stacks[id] = { ...this.stack(id), [slot]: list };
  }

  defaultOf(id: string, block: string, key: string) {
    return (
      POD_DEFAULTS[id]?.[block]?.[key] ??
      PARAMS[block]?.find((x) => x.key === key)?.value ??
      0
    );
  }
  get(id: string, block: string, key: string, defaults = false) {
    return (
      (defaults ? undefined : this.values[id]?.[block]?.[key]) ??
      this.defaultOf(id, block, key)
    );
  }
  set(id: string, block: string, key: string, v: number) {
    const pod = { ...(this.values[id] ?? {}) };
    pod[block] = { ...(pod[block] ?? {}), [key]: v };
    this.values[id] = pod;
  }
  /** The edits as last saved, per pod (serialised). */
  private saved = $state<Record<string, string>>({});
  private snapshot(id: string) {
    return JSON.stringify([this.values[id] ?? {}, this.stacks[id] ?? null]);
  }
  isDirty(id: string) {
    return this.snapshot(id) !== (this.saved[id] ?? JSON.stringify([{}, null]));
  }
  /** Keep the edits as the next version. */
  save(id: string) {
    this.saved[id] = this.snapshot(id);
    this.bumps[id] = (this.bumps[id] ?? 0) + 1;
    return this.version(id);
  }
  /** Back to the last saved version. */
  discard(id: string) {
    const [values, stacks] = JSON.parse(
      this.saved[id] ?? JSON.stringify([{}, null]),
    );
    this.values[id] = values;
    if (stacks) this.stacks[id] = stacks;
    else delete this.stacks[id];
  }
  version(id: string, ahead = 0) {
    const n =
      +(this.pod(id).version.match(/\d+/)?.[0] ?? 1) + (this.bumps[id] ?? 0);
    return `v${n + ahead}`;
  }

  /** The block's settings as one short line, e.g. "0.75% · ×0.5". */
  setting(id: string, block: string): string {
    const ps = PARAMS[block];
    if (!ps?.length) return blockById(block)?.setting ?? "";
    if (block === "ladder")
      return `−${this.get(id, block, "at1")}% ×${this.get(id, block, "mult1")} · −${this.get(id, block, "at2")}% ×${this.get(id, block, "mult2")}`;
    return ps.map((x) => fmt(this.get(id, block, x.key), x.unit)).join(" · ");
  }

  ladder(id: string, defaults = false): Step[] {
    if (!this.has(id, "ladder", defaults)) return [];
    const g = (k: string) => this.get(id, "ladder", k, defaults);
    return [
      { at: g("at1"), mult: g("mult1") },
      { at: g("at2"), mult: g("mult2") },
    ];
  }
  kill(id: string, defaults = false) {
    return this.get(id, "kill", "kill", defaults);
  }

  /** One sample trade walked through the pod, block by block. */
  trail(id: string, defaults = false): { step: string; usd: number }[] {
    const s = { ...SAMPLE, ...this.sample };
    const stopDist = (s.entry - s.stop) / s.entry;
    const g = (b: string, k: string) => this.get(id, b, k, defaults);
    const sizer = this.stack(id, defaults).sizer[0];
    let usd: number;
    let label: string;
    switch (sizer) {
      case "fixed-usd":
        usd = g(sizer, "usd");
        label = `Sizer · ${fmt(usd, "$")} a trade`;
        break;
      case "vol-target":
        usd = (s.equity * g(sizer, "vol")) / 100 / 0.032;
        label = `Sizer · ${g(sizer, "vol")}% daily move`;
        break;
      case "kelly":
        usd =
          (s.equity * Math.min(g(sizer, "cap"), 8 * g(sizer, "frac"))) /
          100 /
          stopDist;
        label = `Sizer · Kelly ×${g(sizer, "frac")}`;
        break;
      case "model-sizer":
        usd = (s.equity * g(sizer, "ceiling") * 0.7) / 100 / stopDist;
        label = `Sizer · model under ${g(sizer, "ceiling")}%`;
        break;
      default:
        usd = (s.equity * g("fixed-frac", "risk")) / 100 / stopDist;
        label = `Sizer · ${g("fixed-frac", "risk")}% risk to the stop`;
    }
    const out = [{ step: label, usd }];
    const throttle = (step: string, mult: number) => {
      usd *= mult;
      out.push({ step, usd });
    };
    for (const t of this.stack(id, defaults).throttles) {
      if (t === "ladder") {
        const m = ladderMult(s.dip, this.ladder(id, defaults));
        throttle(`Drawdown ladder ×${m} at −${s.dip}%`, m);
      } else if (t === "thin-hours") {
        const m = s.weekend ? g(t, "mult") : 1;
        throttle(`Thin hours${s.weekend ? "" : " · weekday"} ×${m}`, m);
      } else if (t === "regime") {
        throttle(`Regime (chop) ×${g(t, "chop")}`, g(t, "chop"));
      } else if (t === "vol-spike") {
        throttle("Volatility spike · not now ×1", 1);
      }
    }
    if (this.has(id, "caps", defaults)) {
      const cap = (s.equity * g("caps", "coin")) / 100;
      if (usd > cap) {
        usd = cap;
        out.push({ step: `Caps · ${g("caps", "coin")}% in one coin`, usd });
      } else out.push({ step: "Caps · within limits", usd });
    }
    const qty = Math.floor(usd / s.entry / s.lot) * s.lot;
    const fee = qty * s.entry * s.fee;
    out.push({
      step: `Venue fit · ${qty.toFixed(5)} BTC, fee $${fee.toFixed(2)}`,
      usd: qty * s.entry,
    });
    return out;
  }

  /** Size of a trade relative to the pod's defaults (1 = unchanged). */
  scale(id: string): number {
    // The sizer, plus the throttles that are not the ladder (the replay
    // applies the ladder itself), each weighted by how often it bites.
    const k = (defaults: boolean) => {
      const g = (b: string, key: string) => this.get(id, b, key, defaults);
      let m = this.trail(id, defaults)[0].usd || 1;
      for (const t of this.stack(id, defaults).throttles) {
        if (t === "thin-hours") m *= 1 - (2 / 7) * (1 - g(t, "mult"));
        if (t === "regime")
          m *= 1 - 0.3 * (1 - g(t, "chop")) - 0.05 * (1 - g(t, "crash"));
        if (t === "vol-spike")
          m *= 1 - 0.05 * (1 - g(t, "mult")) * (g(t, "hours") / 2);
      }
      return m;
    };
    return k(false) / k(true);
  }

  /** The pod's test curve replayed with its current settings. */
  equity(id: string): { curve: number[]; stoodDown: boolean } {
    const r = replay(POD_EQUITY[id], {
      scale: this.scale(id),
      made: this.ladder(id, true),
      ladder: this.ladder(id),
      killAt: this.kill(id),
    });
    return { curve: r.curve, stoodDown: r.stoodDownAt !== null };
  }

  fan(id: string) {
    const f = FAN[id];
    // Removing the ladder widens the fan; adding one narrows it.
    const ladder =
      Number(this.has(id, "ladder", true)) - Number(this.has(id, "ladder"));
    const k = this.scale(id) * 1.25 ** ladder;
    const kill = this.kill(id);
    const pKill = Math.min(
      99,
      Math.max(0.1, f.pKill * k * k * (this.kill(id, true) / kill) ** 2),
    );
    return {
      p5: f.p5.map((v) => v * k),
      p50: f.p50.map((v) => v * k),
      p95: f.p95.map((v) => v * k),
      pKill: Math.round(pKill * 10) / 10,
      kill,
    };
  }

  /** A stress cell under the current settings; null if never run. */
  stress(id: string, scenario: string): StressCell | null {
    const base = STRESS_GRID[id]?.[scenario] ?? this.ran[id]?.[scenario];
    if (!base) return null;
    const k = this.scale(id);
    const room =
      (Math.abs(base.loss) / Math.max(base.ofRoom, 0.01)) *
      (this.kill(id) / this.kill(id, true));
    const raw = Math.abs(base.loss) * k;
    const loss = Math.min(raw, room);
    const stoodDown = raw >= room;
    return {
      loss: -Math.round(loss / 10) * 10,
      ofRoom: Math.min(1, loss / room),
      fired: stoodDown ? "Kill line" : base.fired,
      stoodDown,
    };
  }
  /** Run a scenario the demo has no result for: a made-up but stable cell. */
  run(id: string, scenario: string) {
    const seed = [...(id + scenario)].reduce((a, c) => a + c.charCodeAt(0), 0);
    const ofRoom = 0.2 + ((seed % 50) / 100) * (id === "classic" ? 1.4 : 1);
    this.ran[id] = {
      ...(this.ran[id] ?? {}),
      [scenario]: {
        loss: -Math.round((ofRoom * 4000) / 10) * 10,
        ofRoom: Math.min(1, ofRoom),
        fired: ofRoom > 0.6 ? "Daily stop" : "Health brake",
        stoodDown: ofRoom >= 1,
      },
    };
  }

  /** Head to head measures under the current settings. */
  attr(attrId: string, id: string): number {
    const a = POD_ATTRS.find((x) => x.id === attrId)!;
    const v = a.values[id];
    const e = this.equity(id);
    if (attrId === "profit")
      return Math.round((20000 * growth(e.curve)) / 1000) * 10;
    if (attrId === "dip") return -Math.round(deepestDip(e.curve));
    if (attrId === "crash") return Math.round((v * this.scale(id)) / 10) * 10;
    if (attrId === "kill") return this.fan(id).pKill;
    return v;
  }

  paper(podId: string) {
    const run = PAPER_RUNS.find((r) => r.pod === podId) ?? PAPER_RUNS[0];
    const of = run.of + (this.paperExtra[run.pod] ?? 0);
    const stopped = !!this.paperStopped[run.pod];
    const paused = !!this.paperPaused[run.pod];
    const checks = run.checks.map((c) =>
      c.label === "Soak time"
        ? { ...c, done: run.day >= of, note: `Day ${run.day} of ${of}` }
        : c,
    );
    return {
      ...run,
      of,
      checks,
      paused,
      stopped,
      ready: !stopped && checks.every((c) => c.done),
    };
  }
}

export const podModel = new PodModel();
