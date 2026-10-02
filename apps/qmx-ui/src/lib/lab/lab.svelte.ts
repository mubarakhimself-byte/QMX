/**
 * Lab chrome state: which layout is open, its tiles (edits are kept per
 * machine), what each link group has selected, and runs ticked for compare.
 * Layout and selection are client-only; runs and assets come from the
 * daemon once it is wired (demo data until then).
 */
import {
  pane,
  parseLayouts,
  split,
  type LinkGroup,
  type TileLayout,
} from "$lib/workbench/tiles/tiles";

// Every layout opens with the same Resources tile on the left (operator,
// 2026-10-02); the rest is only what that kind of work needs.
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
];

const KEY = "qmx.lab.layouts.v2";
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
  /** Show only work on one machine (null = everywhere). */
  envFilter = $state<string | null>(null);

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
    this.stored = this.stored.filter((s) => s.id !== id);
    if (!this.isBuiltin(id) && this.activeId === id) this.activeId = "build";
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
