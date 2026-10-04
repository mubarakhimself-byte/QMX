/**
 * Mini-app screens as data (mini-app SDK, UI layer, stage 1). A mini app or
 * the copilot describes a panel as a flat map of elements drawn only from
 * QMX's own catalog; QMX validates it and draws it in its own style. No code
 * from the author runs in the QMX window. Shape follows json-render
 * (`{ root, elements }`), registration fields follow OpenBB's widgets.json
 * (title, size range, refresh). Research: scratchpad
 * miniapp-sdk-ui-research.md and bb-t3code-research.md (2026-10-04).
 */

export type SpecElement = {
  type: string;
  props?: Record<string, unknown>;
  children?: string[];
};

export type PanelSpec = {
  /** Shown in the tile header. */
  title: string;
  /** Plain sentence for people and the copilot. */
  description?: string;
  /** Smallest size it still reads well at, in grid cells (OpenBB-style). */
  size?: { minW: number; minH: number };
  /** Where its data comes from: an operation or stream the host serves, never a URL. */
  data?: string;
  root: string;
  elements: Record<string, SpecElement>;
};

/** Every type a spec may use, with its required props. The host draws these. */
export const SPEC_CATALOG: Record<
  string,
  { required: string[]; children: boolean; note: string }
> = {
  Stack: { required: [], children: true, note: "Children in a column or row" },
  Grid: { required: [], children: true, note: "Children in equal columns" },
  Heading: { required: ["text"], children: false, note: "A section title" },
  Text: { required: ["text"], children: false, note: "A sentence or two" },
  Metric: {
    required: ["label", "value"],
    children: false,
    note: "A big number with a label; tone up, down or plain",
  },
  Table: {
    required: ["columns", "rows"],
    children: false,
    note: "Rows of values; numbers align right",
  },
  LineChart: {
    required: ["series"],
    children: false,
    note: "One or more lines on one axis",
  },
  Badge: { required: ["text"], children: false, note: "A short status word" },
  Callout: {
    required: ["text"],
    children: false,
    note: "A highlighted note: info, warning or danger",
  },
  Button: {
    required: ["label", "action"],
    children: false,
    note: "Runs an operation the host owns (by id), never code",
  },
};

export const LIMITS = { elements: 60, depth: 6 };

/** Problems that stop a spec from drawing; empty means it is safe to draw. */
export function validate(spec: unknown): string[] {
  const errors: string[] = [];
  if (!spec || typeof spec !== "object") return ["Not a panel description"];
  const s = spec as Partial<PanelSpec>;
  if (typeof s.title !== "string" || !s.title.trim()) errors.push("No title");
  if (!s.elements || typeof s.elements !== "object")
    return [...errors, "No elements"];
  const ids = Object.keys(s.elements);
  if (ids.length > LIMITS.elements)
    errors.push(`Too many elements (${ids.length} > ${LIMITS.elements})`);
  if (typeof s.root !== "string" || !s.elements[s.root])
    errors.push("Root element missing");
  for (const [id, el] of Object.entries(s.elements)) {
    const def = SPEC_CATALOG[el?.type];
    if (!def) {
      errors.push(`${id}: "${el?.type}" is not in QMX's catalog`);
      continue;
    }
    for (const r of def.required)
      if (el.props?.[r] === undefined) errors.push(`${id}: needs ${r}`);
    if (el.children?.length && !def.children)
      errors.push(`${id}: ${el.type} cannot hold children`);
    for (const c of el.children ?? [])
      if (!s.elements[c]) errors.push(`${id}: child "${c}" is missing`);
  }
  // Depth and cycles, from the root.
  const walk = (id: string, depth: number, seen: Set<string>) => {
    if (depth > LIMITS.depth) {
      errors.push(`Nested deeper than ${LIMITS.depth}`);
      return;
    }
    if (seen.has(id)) {
      errors.push(`"${id}" contains itself`);
      return;
    }
    const next = new Set(seen).add(id);
    for (const c of s.elements?.[id]?.children ?? [])
      if (s.elements?.[c]) walk(c, depth + 1, next);
  };
  if (typeof s.root === "string" && s.elements[s.root])
    walk(s.root, 1, new Set());
  return [...new Set(errors)];
}

/** A sample the copilot "builds" in the demo: weekend risk for the momentum pods. */
export const SAMPLE_PANEL: PanelSpec = {
  title: "Weekend risk",
  description:
    "How the momentum pods did on weekends, and how much the weekend throttle saved.",
  size: { minW: 3, minH: 3 },
  data: "pod.test.weekend_breakdown",
  root: "page",
  elements: {
    page: { type: "Stack", children: ["metrics", "chart", "table", "note"] },
    metrics: {
      type: "Grid",
      props: { columns: 3 },
      children: ["m1", "m2", "m3"],
    },
    m1: {
      type: "Metric",
      props: { label: "Worst weekend, before", value: "−$1,240", tone: "down" },
    },
    m2: {
      type: "Metric",
      props: { label: "Worst weekend, after", value: "−$560", tone: "up" },
    },
    m3: {
      type: "Metric",
      props: { label: "Profit given up", value: "$380", tone: "plain" },
    },
    chart: {
      type: "LineChart",
      props: {
        series: [
          { label: "Trend rider", seed: 202, color: "var(--chart-2)" },
          { label: "Weekend rider", seed: 207, color: "var(--primary)" },
        ],
      },
    },
    table: {
      type: "Table",
      props: {
        columns: ["Weekend", "Trend rider", "Weekend rider"],
        rows: [
          ["Nov 12 2022 (FTX)", "−$1,240", "−$560"],
          ["Mar 9 2024", "−$610", "−$300"],
          ["Aug 3 2024", "−$480", "−$250"],
        ],
      },
    },
    note: {
      type: "Callout",
      props: {
        tone: "info",
        text: "Drawn by QMX from a description; no code from the copilot runs in this window.",
      },
    },
  },
};
