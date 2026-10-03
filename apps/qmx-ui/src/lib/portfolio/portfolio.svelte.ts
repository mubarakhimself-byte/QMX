/**
 * Portfolio chrome state: layouts, the selected Book and promotion, which
 * world is shown (live, paper or both: a view filter, never a control; the
 * docs forbid a generic LIVE/PAPER toggle), and which node is in view.
 */
import { LayoutStore } from "$lib/workbench/tiles/store.svelte";
import { pane, split, type TileLayout } from "$lib/workbench/tiles/tiles";

const accounts = (id: string) => pane(id, "accounts");

export const PORTFOLIO_LAYOUTS: TileLayout[] = [
  {
    id: "risk",
    name: "Risk",
    root: split("row", [
      [accounts("r-acc"), 15],
      [
        split("col", [
          [pane("r-grid", "risk", "amber"), 58],
          [
            split("row", [
              [pane("r-exposure", "exposure"), 50],
              [pane("r-news", "news"), 50],
            ]),
            42,
          ],
        ]),
        59,
      ],
      [
        split("col", [
          [pane("r-book", "book", "amber"), 62],
          [pane("r-rules", "rules", "amber"), 38],
        ]),
        26,
      ],
    ]),
    docked: [],
  },
  {
    id: "books",
    name: "Books",
    root: split("row", [
      [pane("b-wall", "wall", "amber"), 62],
      [
        split("col", [
          [pane("b-book", "book", "amber"), 58],
          [pane("b-approvals", "approvals"), 42],
        ]),
        38,
      ],
    ]),
    docked: [],
  },
  {
    id: "live",
    name: "Live",
    root: split("col", [
      [
        split("row", [
          [pane("l-chart", "chart"), 64],
          [pane("l-control", "control"), 36],
        ]),
        56,
      ],
      [
        split("row", [
          [pane("l-positions", "positions"), 68],
          [pane("l-nodes", "nodes"), 32],
        ]),
        44,
      ],
    ]),
    docked: [],
  },
  {
    id: "promotions",
    name: "Promotions",
    root: split("row", [
      [pane("p-lanes", "promotions", "teal"), 58],
      [
        split("col", [
          [pane("p-card", "signing", "teal"), 60],
          [pane("p-approvals", "approvals"), 40],
        ]),
        42,
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
          [pane("m-chart", "chart"), 60],
          [pane("m-news", "news"), 40],
        ]),
        50,
      ],
    ]),
    docked: [],
  },
  {
    id: "allocate",
    name: "Allocate",
    root: split("row", [
      [pane("a-opt", "allocate"), 64],
      [
        split("col", [
          [pane("a-corr", "correlation"), 55],
          [pane("a-exp", "exposure"), 45],
        ]),
        36,
      ],
    ]),
    docked: [],
  },
];

class PortfolioState {
  layouts = new LayoutStore("qmx.portfolio.layouts", PORTFOLIO_LAYOUTS);
  book = $state("fx-core");
  promotion = $state("pr-1");
  world = $state<"all" | "live" | "paper">("all");
  copilotOpen = $state(false);
  templatesOpen = $state(false);
}

export const portfolio = new PortfolioState();
