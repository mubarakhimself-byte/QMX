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

const KEY = "qmx.home.ticker.v2";
function loadTicker(): string[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    /* storage unavailable */
  }
  return ["XAUUSD", "US500", "NAS100", "EURUSD", "USOIL", "BTC", "ETH"];
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
