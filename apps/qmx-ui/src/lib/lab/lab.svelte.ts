/**
 * Lab chrome state: which layout is open, its tiles (edits are kept per
 * machine), what each link group has selected, and runs ticked for compare.
 * Layout and selection are client-only; runs and assets come from the
 * daemon once it is wired (demo data until then).
 */
import { envById } from "./demo";
import {
  pane,
  parseLayouts,
  split,
  type LinkGroup,
  type TileLayout,
} from "$lib/workbench/tiles/tiles";

// Every strategy layout opens with the same Resources tile on the left
// (operator, 2026-10-02); pod layouts open with Pod resources instead, because
// a pod's ingredients are different (operator, 2026-10-03).
const resources = (id: string) => pane(id, "resources");

export const BUILTIN_LAYOUTS: TileLayout[] = [
  {
    id: "build",
    name: "Build",
    root: split("row", [
      [resources("b-res"), 18],
      [
        split("col", [
          [
            split("row", [
              [pane("b-editor", "editor", "violet"), 72],
              [pane("b-inspector", "inspector", "violet"), 28],
            ]),
            72,
          ],
          [pane("b-logs", "logs", "amber"), 28],
        ]),
        82,
      ],
    ]),
    docked: [],
  },
  {
    id: "test",
    name: "Test",
    root: split("row", [
      [resources("t-res"), 17],
      [
        split("col", [
          [pane("t-matrix", "matrix", "amber"), 56],
          [pane("t-runs", "runs", "amber"), 44],
        ]),
        50,
      ],
      [
        split("col", [
          [pane("t-equity", "equity", "amber"), 46],
          [pane("t-robust", "robustness", "amber"), 54],
        ]),
        33,
      ],
    ]),
    docked: [],
  },
  {
    id: "train",
    name: "Train",
    root: split("row", [
      [resources("tr-res"), 20],
      [
        split("col", [
          [pane("tr-training", "training"), 66],
          [pane("tr-logs", "logs", "amber"), 34],
        ]),
        80,
      ],
    ]),
    docked: [],
  },
  {
    id: "compare",
    name: "Compare",
    root: split("row", [
      [resources("c-res"), 17],
      [pane("c-runs", "runs", "teal"), 35],
      [
        split("col", [
          [pane("c-equity", "equity", "teal"), 50],
          [pane("c-compare", "compare", "teal"), 50],
        ]),
        48,
      ],
    ]),
    docked: [],
  },
  // The Pods bench (operator, 2026-10-03): a pod needs designing, testing
  // and a paper run before money. Comparing rivals and splitting money
  // across pods live inside Test; Pod resources replace the strategy ones.
  {
    id: "pod-design",
    name: "Design",
    group: "pods",
    root: split("row", [
      [pane("pd-res", "podres"), 18],
      [pane("pd-stack", "podstack", "violet"), 46],
      [
        split("col", [
          [pane("pd-block", "block", "violet"), 55],
          [pane("pd-trail", "sizetrail", "violet"), 45],
        ]),
        36,
      ],
    ]),
    docked: [],
  },
  {
    id: "pod-test",
    name: "Test",
    group: "pods",
    root: split("row", [
      [pane("pt-res", "podres"), 18],
      [
        split("col", [
          [pane("pt-equity", "podequity", "teal"), 52],
          [pane("pt-stress", "stress", "teal"), 48],
        ]),
        50,
      ],
      [
        split("col", [
          [pane("pt-h2h", "headtohead", "teal"), 58],
          [pane("pt-fan", "fan", "teal"), 42],
        ]),
        32,
      ],
      [pane("pt-int", "interventions", "teal"), 20],
    ]),
    docked: ["pt-int"],
  },
  {
    id: "pod-paper",
    name: "Paper",
    group: "pods",
    root: split("row", [
      [pane("pp-res", "podres"), 18],
      [
        split("col", [
          [pane("pp-run", "paperrun", "amber"), 55],
          [pane("pp-feed", "paperfeed", "amber"), 45],
        ]),
        54,
      ],
      [
        split("col", [
          [pane("pp-grad", "graduate", "amber"), 55],
          [pane("pp-int", "interventions", "amber"), 45],
        ]),
        28,
      ],
    ]),
    docked: [],
  },
];

const KEY = "qmx.lab.layouts.v6";
const clone = <T>(v: T): T => JSON.parse(JSON.stringify(v)) as T;

function load(): TileLayout[] {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? parseLayouts(JSON.parse(raw), () => true) : [];
  } catch {
    return [];
  }
}

class LabState {
  /** Edited copies of built-ins (same id) plus the operator's own layouts. */
  stored = $state<TileLayout[]>(load());
  activeId = $state("build");
  editing = $state(false);
  /** Selection per link group (a run id, a step id …). */
  selected = $state<Record<LinkGroup, string | null>>({
    violet: "model",
    amber: "run-441",
    teal: "run-441",
  });
  /** Runs ticked for compare. */
  ticked = $state<string[]>(["run-441", "run-502", "run-508"]);
  copilotOpen = $state(false);
  /** Pods in the Lab: the one being built, its selected block, and pods ticked for tests. */
  labPod = $state("trend");
  block = $state("kill");
  podsTicked = $state<string[]>(["classic", "trend", "voltarget"]);
  /** Bots and stress scenarios a pod test runs over. */
  botsTicked = $state<string[]>(["btc-breakout", "eth-trend", "sol-mom"]);
  stressTicked = $state<string[]>([
    "flash",
    "outage",
    "depeg",
    "weekend",
    "ftx",
    "bear",
    "mine-1",
  ]);
  /** "Run together": how a test splits money across the ticked pods (%). */
  mix = $state<Record<string, number>>({
    classic: 25,
    trend: 35,
    voltarget: 40,
  });
  together = $state(false);
  /** Text dropped into the Lab copilot's composer (e.g. "build a stress scenario"). */
  copilotSeed = $state("");
  /** The last layout open on each bench, so switching back lands there. */
  private lastOn = $state<Record<string, string>>({
    strategies: "build",
    pods: "pod-design",
  });
  /**
   * The machine the Lab is looking at (null = all machines), like a remote
   * window in VS Code: picking one connects first, then every tile shows
   * only that machine's work.
   */
  machine = $state<string | null>(null);
  connection = $state<{
    target: string;
    step: number;
    failed: string | null;
  } | null>(null);
  /** A copilot-led walk through the Lab (layout per step). */
  guide = $state<{
    title: string;
    steps: { layout: string; text: string }[];
    at: number;
  } | null>(null);

  /** Placement checks in the CT-46 order the docs use. */
  static CHECKS = ["Reachable", "Signed in", "Healthy"];

  connect(id: string | null) {
    if (id === null || id === this.machine) {
      this.machine = id;
      this.connection = null;
      return;
    }
    const env = envById(id);
    this.connection = { target: id, step: 0, failed: null };
    const tick = (step: number) => {
      if (!this.connection || this.connection.target !== id) return;
      if (env?.status === "offline" && step === 0) {
        this.connection = {
          target: id,
          step: 0,
          failed: `${env.name} is offline. Start it from its provider, or pick another machine.`,
        };
        return;
      }
      if (step >= LabState.CHECKS.length) {
        this.machine = id;
        this.connection = null;
        return;
      }
      this.connection = { target: id, step: step + 1, failed: null };
      setTimeout(() => tick(step + 1), 380);
    };
    setTimeout(() => tick(0), 300);
  }

  startGuide(g: { title: string; steps: { layout: string; text: string }[] }) {
    this.guide = { ...g, at: 0 };
    this.activeId = g.steps[0].layout;
  }

  guideStep(delta: number) {
    if (!this.guide) return;
    const at = this.guide.at + delta;
    if (at < 0) return;
    if (at >= this.guide.steps.length) {
      this.guide = null;
      return;
    }
    this.guide = { ...this.guide, at };
    this.activeId = this.guide.steps[at].layout;
  }

  /** Strategies or Pods: follows the open layout. */
  get bench(): string {
    return this.active.group ?? "strategies";
  }

  /** The layouts on the open bench, for the header. */
  get benchLayouts(): TileLayout[] {
    return this.layouts.filter((l) => (l.group ?? "strategies") === this.bench);
  }

  open(id: string) {
    this.lastOn[this.bench] = this.activeId;
    this.activeId = id;
  }

  setBench(b: string) {
    if (b === this.bench) return;
    this.lastOn[this.bench] = this.activeId;
    const target = this.lastOn[b];
    this.activeId = this.layouts.some((l) => l.id === target)
      ? target
      : (this.layouts.find((l) => (l.group ?? "strategies") === b)?.id ??
        "build");
  }

  /** Open the Lab copilot with a message drafted. */
  ask(text: string) {
    this.copilotOpen = true;
    this.copilotSeed = text;
  }

  get layouts(): TileLayout[] {
    const builtins = BUILTIN_LAYOUTS.map(
      (b) => this.stored.find((s) => s.id === b.id) ?? b,
    );
    const own = this.stored.filter(
      (s) => !BUILTIN_LAYOUTS.some((b) => b.id === s.id),
    );
    return [...builtins, ...own];
  }

  get active(): TileLayout {
    return this.layouts.find((l) => l.id === this.activeId) ?? this.layouts[0];
  }

  isBuiltin(id: string) {
    return BUILTIN_LAYOUTS.some((b) => b.id === id);
  }

  isEdited(id: string) {
    return this.isBuiltin(id) && this.stored.some((s) => s.id === id);
  }

  private persist() {
    try {
      localStorage.setItem(KEY, JSON.stringify(this.stored));
    } catch {
      /* storage unavailable: edits last for this window */
    }
  }

  update(next: TileLayout) {
    this.stored = [...this.stored.filter((s) => s.id !== next.id), next];
    this.persist();
  }

  /** Add a layout built elsewhere (e.g. the guided start) and open it. */
  addLayout(l: TileLayout) {
    const copy = { ...clone(l), id: `u-${Date.now().toString(36)}` };
    this.stored = [...this.stored, copy];
    this.activeId = copy.id;
    this.persist();
    return copy;
  }

  saveAs(name: string) {
    const copy: TileLayout = {
      ...clone(this.active),
      id: `u-${Date.now().toString(36)}`,
      name: name.trim().slice(0, 40) || "My layout",
    };
    this.stored = [...this.stored, copy];
    this.activeId = copy.id;
    this.persist();
    return copy;
  }

  /** Built-ins return to their default; your own layouts are deleted. */
  reset(id: string) {
    const bench = this.bench;
    this.stored = this.stored.filter((s) => s.id !== id);
    if (!this.isBuiltin(id) && this.activeId === id)
      this.activeId =
        BUILTIN_LAYOUTS.find((l) => (l.group ?? "strategies") === bench)?.id ??
        "build";
    this.persist();
  }

  select(link: LinkGroup | undefined, id: string) {
    if (link) this.selected[link] = id;
    else this.selected.amber = id;
  }

  selectedFor(link: LinkGroup | undefined): string | null {
    return this.selected[link ?? "amber"];
  }

  toggleTick(id: string) {
    this.ticked = this.ticked.includes(id)
      ? this.ticked.filter((t) => t !== id)
      : [...this.ticked, id].slice(-4);
  }
}

export const lab = new LabState();
