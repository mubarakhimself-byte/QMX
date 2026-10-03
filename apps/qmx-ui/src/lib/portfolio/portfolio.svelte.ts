/**
 * Portfolio chrome state: layouts, the selected pod and road-to-live
 * candidate, and which world is shown (live, paper or both: a view filter,
 * never a control; the docs forbid a generic LIVE/PAPER toggle).
 */
import { LayoutStore } from "$lib/workbench/tiles/store.svelte";
import { pane, split, type TileLayout } from "$lib/workbench/tiles/tiles";

export const PORTFOLIO_LAYOUTS: TileLayout[] = [
  {
    id: "overview",
    name: "Overview",
    root: split("row", [
      [pane("o-acc", "accounts"), 15],
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
        57,
      ],
      [pane("o-pod", "pod", "amber"), 28],
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
}

export const portfolio = new PortfolioState();
