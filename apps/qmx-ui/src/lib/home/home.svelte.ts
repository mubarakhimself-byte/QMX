/**
 * Home (rethink, 2026-10-04): the same tile board as the Lab and Portfolio
 * (one widget system, not two), with built-in tabs and your own saved tabs,
 * an editable ticker and an inbox of what needs you. Demo data comes from
 * the other screens' samples so every link opens the real place.
 */
import { LayoutStore } from "$lib/workbench/tiles/store.svelte";
import { pane, split, type TileLayout } from "$lib/workbench/tiles/tiles";

export const HOME_LAYOUTS: TileLayout[] = [
  {
    id: "today",
    name: "Today",
    root: split("row", [
      [
        split("col", [
          [pane("t-needs", "needs"), 55],
          [pane("t-going", "going"), 45],
        ]),
        30,
      ],
      [
        split("col", [
          [pane("t-pods", "pods"), 52],
          [pane("t-news", "events"), 48],
        ]),
        44,
      ],
      [
        split("col", [
          [pane("t-markets", "markets"), 55],
          [pane("t-cal", "calendar"), 45],
        ]),
        26,
      ],
    ]),
    docked: [],
  },
  {
    id: "markets",
    name: "Markets",
    root: split("row", [
      [
        split("col", [
          [pane("m-screener", "screener"), 60],
          [pane("m-markets", "markets"), 40],
        ]),
        62,
      ],
      [pane("m-news", "events"), 38],
    ]),
    docked: [],
  },
  {
    id: "research",
    name: "Research",
    root: split("row", [
      [pane("r-recent", "recent"), 40],
      [
        split("col", [
          [pane("r-going", "going"), 50],
          [pane("r-news", "events"), 50],
        ]),
        60,
      ],
    ]),
    docked: [],
  },
];

export const COINS = [
  { sym: "BTC", px: 64210, chg: 1.83 },
  { sym: "ETH", px: 3118, chg: 2.41 },
  { sym: "SOL", px: 141.2, chg: -3.1 },
  { sym: "AVAX", px: 27.6, chg: 0.9 },
  { sym: "LINK", px: 12.3, chg: 3.2 },
  { sym: "DOGE", px: 0.1214, chg: -1.4 },
  { sym: "XRP", px: 0.5891, chg: 0.6 },
  { sym: "BNB", px: 581.4, chg: 0.4 },
  { sym: "DXY", px: 104.2, chg: -0.18 },
  { sym: "EURUSD", px: 1.0883, chg: 0.22 },
  { sym: "Gold", px: 2384.1, chg: -0.22 },
];

const KEY = "qmx.home.ticker";
function loadTicker(): string[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    /* storage unavailable */
  }
  return ["BTC", "ETH", "SOL", "AVAX", "LINK", "DXY"];
}

class HomeState {
  layouts = new LayoutStore("qmx.home.layouts.v1", HOME_LAYOUTS);
  ticker = $state<string[]>(loadTicker());

  setTicker(list: string[]) {
    this.ticker = list;
    try {
      localStorage.setItem(KEY, JSON.stringify(list));
    } catch {
      /* storage unavailable */
    }
  }
}

export const home = new HomeState();

export const fmtPx = (v: number) =>
  v >= 1000
    ? v.toLocaleString("en-US", { maximumFractionDigits: 0 })
    : v >= 2
      ? v.toFixed(2)
      : v.toFixed(4);
