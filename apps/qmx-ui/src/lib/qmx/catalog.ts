/**
 * QMX component catalog: the host-owned list of building blocks a mini app
 * may be composed from (UI COMPONENT-CONTRACTS §4, json-render "host-owned
 * catalog"). The copilot's build_app tool reads this to compose a view;
 * the host renders it. Widgets never get wire access, and actions are op_ids
 * the host dispatches, never code.
 *
 * Keep descriptions plain: they are what the model reads.
 */

export type PropSpec = {
  type: "string" | "number" | "boolean" | "array" | "object" | "enum";
  description: string;
  required?: boolean;
  options?: readonly string[];
};

export type CatalogEntry = {
  type: string;
  group: "Frame" | "Data" | "Chart" | "Card" | "Copilot" | "State";
  description: string;
  props: Record<string, PropSpec>;
  /** A minimal valid instance, used by the library page and as a model example. */
  example: Record<string, unknown>;
};

export const CATALOG: CatalogEntry[] = [
  {
    type: "WidgetFrame",
    group: "Frame",
    description:
      "The frame every widget sits in: title, readable state, and header controls (refresh, add to copilot, minimise, expand, close). Only controls with a handler appear.",
    props: {
      title: {
        type: "string",
        description: "Short uppercase-rendered title.",
        required: true,
      },
      state: {
        type: "enum",
        description: "What the widget can show right now.",
        options: [
          "ready",
          "loading",
          "empty",
          "unavailable",
          "failed",
          "reconnecting",
          "stale",
          "unknown",
        ],
      },
      reason: {
        type: "string",
        description: "Why it is empty, unavailable, failed or stale.",
      },
    },
    example: { title: "Key figures", state: "ready" },
  },
  {
    type: "StatTile",
    group: "Data",
    description:
      "One headline number with a label and a short hint. Shows a dash when there is no value.",
    props: {
      label: {
        type: "string",
        description: "What the number is.",
        required: true,
      },
      value: { type: "string", description: "Formatted value." },
      hint: { type: "string", description: "Context, e.g. change today." },
    },
    example: {
      label: "Paper equity",
      value: "$104,812",
      hint: "+$1,204 today",
    },
  },
  {
    type: "DataTable",
    group: "Data",
    description:
      "The standard table. Columns are text, number (right-aligned, monospaced) or change (signed, coloured, with arrows for colour-blind readers).",
    props: {
      columns: {
        type: "array",
        description: "[{ key, label, kind?, digits? }]",
        required: true,
      },
      rows: {
        type: "array",
        description: "Objects keyed by column key.",
        required: true,
      },
      dense: { type: "boolean", description: "Tighter rows for long lists." },
    },
    example: {
      columns: [
        { key: "sym", label: "Symbol" },
        { key: "last", label: "Last", kind: "number", digits: 4 },
        { key: "chg", label: "Change", kind: "change" },
      ],
      rows: [
        { sym: "EURUSD", last: 1.0883, chg: -0.4 },
        { sym: "GBPUSD", last: 1.2745, chg: 0.12 },
        { sym: "XAUUSD", last: 2384.1, chg: -0.22 },
      ],
    },
  },
  {
    type: "CandleChart",
    group: "Chart",
    description:
      "Financial candlesticks with volume (lightweight-charts). Optional markers show agent signals on specific candles.",
    props: {
      candles: {
        type: "array",
        description: "[{ time, open, high, low, close, volume }]",
        required: true,
      },
      markers: {
        type: "array",
        description: "[{ time, text }] drawn under the candle.",
      },
    },
    example: { candles: "demoCandles(90)", markers: [] },
  },
  {
    type: "Sparkline",
    group: "Chart",
    description:
      "A tiny trend line. Green when the series ends higher than it starts, red otherwise.",
    props: {
      values: {
        type: "array",
        description: "Numbers in time order.",
        required: true,
      },
    },
    example: { values: [3, 4, 3.5, 5, 6, 5.5, 7] },
  },
  {
    type: "AssetCard",
    group: "Card",
    description:
      "Player-card view of a bot, ML model, mini app or workflow: overall rating, tier, stage and six attributes. Ratings come from the asset's metrics.",
    props: {
      asset: {
        type: "object",
        description:
          "{ kind, name, role, stage, rating, attributes:[{key,label,value}], spark? }",
        required: true,
      },
    },
    example: { asset: "DEMO_ASSETS[0]" },
  },
  {
    type: "EmptyState",
    group: "State",
    description:
      "What a surface shows when it has nothing yet: one line, an optional reason and one action.",
    props: {
      title: {
        type: "string",
        description: "What is missing.",
        required: true,
      },
      description: { type: "string", description: "Why, or how to get it." },
    },
    example: {
      title: "No jobs running",
      description: "Backtests and workflows in progress appear here.",
    },
  },
  {
    type: "Composer",
    group: "Copilot",
    description:
      "The message box for any copilot: context chips, Attach and Tools menus, model picker, send. Sending goes through the host's dispatchChat.",
    props: {
      placeholder: { type: "string", description: "Prompt text." },
      refs: {
        type: "array",
        description: "Context chips added from widgets or Library items.",
      },
    },
    example: { placeholder: "Ask about this app…" },
  },
];
