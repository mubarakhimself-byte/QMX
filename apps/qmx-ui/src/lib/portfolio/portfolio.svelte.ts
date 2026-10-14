/**
 * Portfolio chrome state: layouts, the selected pod and road-to-live
 * candidate, and which world is shown (live, paper or both: a view filter,
 * never a control; the docs forbid a generic LIVE/PAPER toggle).
 */
import { LayoutStore } from "$lib/workbench/tiles/store.svelte";
import { pane, split, type TileLayout } from "$lib/workbench/tiles/tiles";
import { CANDIDATES, type Candidate } from "./demo";

export const PORTFOLIO_LAYOUTS: TileLayout[] = [
  {
    id: "overview",
    name: "Overview",
    root: split("row", [
      [pane("o-acc", "accounts"), 14],
      [
        split("col", [
          [pane("o-pods", "pods", "amber"), 56],
          [
            split("row", [
              [pane("o-events", "events"), 58],
              [pane("o-exposure", "exposure"), 42],
            ]),
            44,
          ],
        ]),
        51,
      ],
      [pane("o-pod", "pod", "amber"), 35],
    ]),
    docked: [],
  },
  {
    id: "pods",
    name: "Pods",
    root: split("row", [
      [pane("p-list", "pods", "amber"), 30],
      [pane("p-pod", "pod", "amber"), 70],
    ]),
    docked: [],
  },
  {
    id: "live",
    name: "Live",
    root: split("col", [
      [pane("l-holdings", "holdings"), 52],
      [pane("l-charts", "botcharts"), 48],
    ]),
    docked: [],
  },
  {
    id: "road",
    name: "Road to live",
    root: split("row", [
      [pane("r-road", "road", "teal"), 60],
      [
        split("col", [
          [pane("r-card", "signing", "teal"), 52],
          [pane("r-journal", "journal", "teal"), 48],
        ]),
        40,
      ],
    ]),
    docked: [],
  },
  {
    id: "mis",
    name: "MIS",
    root: split("row", [
      [pane("m-mis", "mis"), 50],
      [
        split("col", [
          [pane("m-charts", "botcharts"), 60],
          [pane("m-events", "events"), 40],
        ]),
        50,
      ],
    ]),
    docked: [],
  },
];

class PortfolioState {
  layouts = new LayoutStore("qmx.portfolio.layouts.v3", PORTFOLIO_LAYOUTS);
  pod = $state("core");
  candidate = $state("avax-mom");
  world = $state<"all" | "live" | "paper">("all");
  copilotOpen = $state(false);
  templatesOpen = $state(false);
  /** Road-to-live moves you made in this session (demo, in the browser). */
  moved = $state<Record<string, { stage: Candidate["stage"]; days: number }>>(
    {},
  );

  get candidates(): Candidate[] {
    return CANDIDATES.map((c) => ({ ...c, ...this.moved[c.entity.id] }));
  }
  /** Sign for live (paper → ready), sign and activate (ready → live), or pull back to paper. */
  advance(id: string) {
    const c = this.candidates.find((x) => x.entity.id === id);
    if (!c) return;
    const next = { paper: "ready", ready: "live", live: "paper" } as const;
    this.moved[id] = {
      stage: next[c.stage],
      days: c.stage === "paper" ? c.days : 0,
    };
  }
}

export const portfolio = new PortfolioState();
