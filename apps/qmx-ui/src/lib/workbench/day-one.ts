/**
 * Day one: what a fresh install shows with demo mode off. One line and the
 * action that fills it (DESIGN-RULES.md rule 1), per board panel, plus the
 * first-run steps on Home. Every board panel must have an entry here; the
 * test fails otherwise.
 */

export type FirstAction = { label: string; href: string };

/** The handful of actions that fill an empty QMX. Paths include their query. */
export const FIRST = {
  broker: { label: "Connect a broker", href: "/settings?tab=brokers" },
  model: { label: "Pick a model provider", href: "/settings?tab=tools" },
  source: { label: "Add a source", href: "/library?shelf=sources" },
  template: {
    label: "Start from a template",
    href: "/library?shelf=templates",
  },
  pod: {
    label: "New pod",
    href: `/copilot?ask=${encodeURIComponent("Build me a new pod for ")}`,
  },
  copilot: { label: "Ask the copilot", href: "/copilot" },
  machine: { label: "Add a machine", href: "/settings?tab=servers" },
  library: { label: "Open the Library", href: "/library" },
} satisfies Record<string, FirstAction>;

export type DayOne = { line: string; action: FirstAction };

const runs = (line: string): DayOne => ({ line, action: FIRST.template });
const pods = (line: string): DayOne => ({ line, action: FIRST.pod });
const broker = (line: string): DayOne => ({ line, action: FIRST.broker });

/** Keyed by panel id across Home, Lab and Portfolio (ids are shared). */
export const DAY_ONE: Record<string, DayOne> = {
  // Home
  needs: { line: "Nothing needs you", action: FIRST.copilot },
  going: { line: "Nothing running", action: FIRST.copilot },
  markets: broker("No markets yet"),
  screener: broker("No market data yet"),
  calendar: { line: "No calendar yet", action: FIRST.source },
  recent: { line: "Nothing opened yet", action: FIRST.library },
  pinned: { line: "Nothing pinned yet", action: FIRST.copilot },
  // Lab, Strategies
  resources: runs("Your toolbox is empty"),
  assets: runs("Your toolbox is empty"),
  editor: runs("Nothing open"),
  inspector: runs("No step to inspect"),
  runs: runs("No runs yet"),
  matrix: runs("No sweeps yet"),
  equity: runs("No runs yet"),
  robustness: runs("No runs to check"),
  compare: runs("No runs to compare"),
  training: runs("No models training"),
  slots: runs("No models yet"),
  data: { line: "No datasets yet", action: FIRST.source },
  compute: { line: "Only this laptop", action: FIRST.machine },
  agents: { line: "No agents yet", action: FIRST.copilot },
  logs: runs("No runs yet"),
  // Lab, Pods
  podstack: pods("No pods yet"),
  block: pods("No pods yet"),
  sizetrail: pods("No trades sized yet"),
  fan: pods("No pods yet"),
  stress: pods("No pods to stress"),
  interventions: pods("No interventions yet"),
  podequity: pods("No pods yet"),
  podres: pods("No pods yet"),
  headtohead: pods("No pods to compare"),
  paperrun: pods("Nothing on paper"),
  paperfeed: pods("Nothing on paper"),
  graduate: pods("Nothing to promote"),
  // Portfolio (Home shares pods and events)
  accounts: broker("No accounts yet"),
  pods: pods("No pods yet"),
  pod: pods("No pods yet"),
  events: { line: "No news yet", action: FIRST.source },
  exposure: broker("Nothing held"),
  botcharts: broker("No bots trading"),
  holdings: broker("Nothing held"),
  positions: broker("No open positions"),
  control: broker("Nothing to stop"),
  correlation: pods("No pods yet"),
  nodes: { line: "No trading servers", action: FIRST.machine },
  road: pods("Nothing on the road to live"),
  signing: pods("Nothing to sign"),
  journal: broker("No trades yet"),
  mis: { line: "No market labelers", action: FIRST.copilot },
};

/** The first-run steps on Home, in order. */
export const GET_STARTED = [
  { id: "broker", ...FIRST.broker },
  { id: "model", ...FIRST.model },
  { id: "source", label: "Add a data source", href: FIRST.source.href },
  {
    id: "start",
    label: "Start a strategy or pod",
    href: FIRST.template.href,
  },
] as const;
export type StepId = (typeof GET_STARTED)[number]["id"];
