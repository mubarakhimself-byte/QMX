// Demo data for the base app. Every noun here exists in the backend today
// (kit/refs/grounding/08-qmx-today-for-design.md); the numbers are samples.
// Places are the two boards (Overview, Trading), the lists of his things,
// and Usage and Settings (reached from the top bar). The things themselves,
// their pages and the demo's decisions live in model.ts and things.svelte.ts.
import type { ListKind } from "./model";

export type State = "needs" | "run" | "up" | "down" | "idle" | "live" | "paper";

export type Row = {
  label: string;
  meta?: string;
  state?: State;
  value?: string;
  tone?: "up" | "down";
  where?: string;
};

// One widget on a board. "card" widgets draw their content from his things
// (see CardBody.svelte); the other kinds carry their own sample content.
export type Panel = {
  id: string;
  title: string;
  icon: string;
  kind: "card" | "list" | "stats" | "table" | "chart" | "jobs";
  grow?: number;
  mode?: "live" | "paper";
  guest?: string; // a card a mini app offers
  rows?: Row[];
  stats?: { label: string; value: string; delta?: string; tone?: "up" | "down" }[];
  cols?: string[];
  table?: string[][];
  series?: number[];
  note?: string;
  jobs?: { total: number; running: number; waiting: number; done: number };
};

export type Place = {
  id: string;
  name: string;
  icon: string;
  // board: widgets in rows (board[row][column]). list: a list of his things.
  // app: a mini app's own page.
  kind: "board" | "list" | "app";
  list?: ListKind;
  foot?: boolean; // reached from the top bar or a count, not the navigation
  purpose: string;
  board: Panel[][];
  // Widgets this board can add that are not on it by default.
  spare?: Panel[];
  first: { title: string; line: string; action: string; steps: string[] };
};

const curve = (seed: number, n = 40, drift = 0.6) => {
  let v = 50;
  let s = seed;
  return Array.from({ length: n }, () => {
    s = (s * 9301 + 49297) % 233280;
    v += (s / 233280 - 0.5 + drift * 0.08) * 9;
    return Math.round(v * 10) / 10;
  });
};

// Every card a board can hold. A mini app can offer one too (guest).
const card = (id: string, title: string, icon: string, extra: Partial<Panel> = {}): Panel => ({ id, title, icon, kind: "card", ...extra });
export const cards: Record<string, Panel> = {
  waiting: card("waiting", "Waiting for you", "inbox", { grow: 1 }),
  since: card("since", "Since you left", "calendar-clock"),
  units: card("units", "Units on paper and live", "candlestick", { grow: 1.15 }),
  pods: card("pods", "Pods", "folder-kanban", { grow: 1 }),
  running: card("running", "Running now", "loader", { grow: 1 }),
  markets: card("markets", "Markets today", "calendar"),
  positions: card("positions", "Open positions", "list"),
  nodes: card("nodes", "Nodes", "server"),
  "g:readings": card("g:readings", "Regime readings", "radar", { guest: "mis" }),
  "t:u-gold": card("t:u-gold", "Gold breakout", "candlestick"),
  "t:u-london": card("t:u-london", "London fade", "candlestick"),
  "t:u-btc": card("t:u-btc", "BTC trend", "candlestick"),
  "t:u-index": card("t:u-index", "Index open drive", "candlestick"),
};
const pick = (...ids: string[]) => ids.map((i) => cards[i]);

const list = (id: string, name: string, icon: string, l: ListKind, purpose: string, foot = false): Place => ({
  id,
  name,
  icon,
  kind: "list",
  list: l,
  foot,
  purpose,
  board: [],
  first: { title: name, line: purpose, action: "", steps: [] },
});

export const places: Place[] = [
  {
    id: "overview",
    name: "Overview",
    icon: "layout-grid",
    kind: "board",
    purpose: "What waits for you, what runs, and how the money is doing.",
    // Columns: what waits for him | his units and their curve | what runs and the markets.
    board: [pick("waiting", "units", "running"), pick("since", "pods", "markets")],
    spare: pick("positions", "nodes", "g:readings"),
    first: {
      title: "Your desk is not open yet",
      line: "Four steps and you have a unit trading on a demo account.",
      action: "Start with the copilot",
      steps: ["Connect an AI provider", "Download a market's history", "Build and test your first unit", "Start a trading node on This PC"],
    },
  },
  {
    id: "trading",
    name: "Trading",
    icon: "activity",
    kind: "board",
    purpose: "Units on paper and live, their positions, and the nodes they trade on.",
    board: [pick("t:u-gold", "t:u-btc", "positions"), pick("t:u-london", "t:u-index", "nodes")],
    spare: pick("pods", "markets", "g:readings"),
    first: {
      title: "Nothing is trading yet",
      line: "A unit shows up here when you promote it to paper.",
      action: "Start a node on This PC",
      steps: ["Sign in to a demo account", "Start the node", "Promote a tested unit to paper"],
    },
  },
  list("units", "Units", "candlestick", "units", "Every unit, where it is in its life on each market."),
  list("sessions", "Sessions", "message-square", "sessions", "Every chat with the copilot, with its helpers and approvals."),
  list("runs", "Runs", "loader", "runs", "Backtests, workflows and helpers, with where each one runs."),
  list("workflows", "Workflows", "workflow", "workflows", "Things that run on a schedule or a trigger."),
  list("library", "Library", "library", "library", "Everything QMX owns, with its history."),
  list("needs", "Needs you", "inbox", "needs", "Proposals, approvals and failures that wait for you.", true),
  {
    id: "usage",
    name: "Usage",
    icon: "gauge",
    kind: "board",
    foot: true,
    purpose: "AI providers, their limits, and which part of QMX uses which model.",
    board: [
      [
        {
          id: "plans",
          title: "Plans and keys",
          icon: "key-round",
          kind: "stats",
          grow: 1.5,
          stats: [
            { label: "Claude Max · 5h", value: "62%" },
            { label: "Claude Max · week", value: "38%" },
            { label: "DeepSeek", value: "$4.12" },
            { label: "OpenRouter", value: "$0.31" },
          ],
        },
        {
          id: "who",
          title: "Who uses what",
          icon: "route",
          kind: "table",
          grow: 1.5,
          cols: ["Who", "Uses", "Set by"],
          table: [
            ["Copilot", "Opus 5.5", "You"],
            ["Workflows", "DeepSeek", "Default"],
            ["Helpers", "Sonnet 5.5", "Default"],
            ["Morning brief", "Haiku 5.5", "You"],
          ],
        },
      ],
      [
        {
          id: "spend",
          title: "Tokens, 7 days",
          icon: "bar-chart-3",
          kind: "chart",
          series: curve(9, 28, 0.2),
          note: "18.4M tokens · estimates, not your bill",
        },
      ],
    ],
    first: {
      title: "No AI provider connected",
      line: "QMX needs one to run the copilot. Your plan or an API key both work.",
      action: "Connect a provider",
      steps: ["Sign in with a plan, or paste a key", "Test it", "The copilot picks it up at once"],
    },
  },
  {
    id: "settings",
    name: "Settings",
    icon: "settings",
    kind: "board",
    foot: true,
    purpose: "Accounts, machines, rules, appearance.",
    board: [
      [
        {
          id: "machines",
          title: "Machines",
          icon: "server",
          kind: "table",
          cols: ["Name", "Role", "Health", "Version"],
          table: [
            ["This PC", "Home", "OK", "0.9.0"],
            ["vps-fra", "Compute, trading node", "OK", "0.9.0"],
          ],
        },
      ],
    ],
    first: {
      title: "Settings",
      line: "Defaults are set. Change anything, any time.",
      action: "Add a machine",
      steps: [],
    },
  },
];
