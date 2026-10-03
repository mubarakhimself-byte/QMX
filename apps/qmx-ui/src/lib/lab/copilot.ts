/**
 * The Lab copilot's own context: Lab tools (QMB procedures, training, panels,
 * compute placement), agents it can hand work to, and Lab attachments.
 * Tools marked new scope have no backend contract yet.
 */
import Boxes from "@lucide/svelte/icons/boxes";
import Table from "@lucide/svelte/icons/table";
import FolderGit2 from "@lucide/svelte/icons/folder-git-2";
import Database from "@lucide/svelte/icons/database";
import LayoutPanelTop from "@lucide/svelte/icons/layout-panel-top";
import type { CopilotContext } from "$lib/workbench/copilot-context";

export const LAB_CONTEXT: CopilotContext = {
  id: "lab",
  tools: [
    {
      id: "qmb.backtest",
      note: "Run a backtest of a published version",
      group: "Test",
    },
    {
      id: "qmb.sweep",
      note: "Markets × timeframes × parameters",
      group: "Test",
    },
    {
      id: "qmb.walk_forward",
      note: "Fit, test the next window, roll",
      group: "Test",
    },
    {
      id: "qmb.robustness",
      note: "Monte Carlo, significance, what-if",
      group: "Test",
    },
    {
      id: "qmb.optimize",
      note: "Search parameters with an overfit check",
      group: "Test",
    },
    {
      id: "lab.train",
      note: "Train or retrain a model",
      group: "Train",
      scope: "new",
    },
    {
      id: "lab.import_model",
      note: "Bring in a model built elsewhere",
      group: "Train",
      scope: "new",
    },
    {
      id: "graph.edit_draft",
      note: "Add, remove or rewire steps in a draft",
      group: "Build",
    },
    { id: "code.edit", note: "Change the bot's Python", group: "Build" },
    {
      id: "lab.add_panel",
      note: "Build a new panel from your data",
      group: "Build",
      scope: "new",
    },
    { id: "compute.place", note: "Choose where a run goes", group: "Compute" },
    {
      id: "data.inspect",
      note: "Read coverage, gaps and schema",
      group: "Data",
    },
  ],
  defaultTools: [
    "qmb.backtest",
    "qmb.sweep",
    "qmb.walk_forward",
    "qmb.robustness",
    "graph.edit_draft",
    "code.edit",
    "data.inspect",
  ],
  targets: [
    {
      id: "researcher",
      name: "Researcher",
      kind: "Quant",
      note: "Finds ideas and evidence in your Library",
      blocked: null,
    },
    {
      id: "analyst",
      name: "Analyst",
      kind: "Quant",
      note: "Runs and reads experiments",
      blocked: null,
    },
    {
      id: "developer",
      name: "Developer",
      kind: "Quant",
      note: "Writes and fixes bot code",
      blocked: "not configured",
    },
  ],
  attach: [
    {
      id: "toolbox",
      label: "From the toolbox",
      note: "Workflow, bot, model, dataset, test",
      icon: Boxes,
      needs: null,
    },
    {
      id: "runs",
      label: "Ticked runs",
      note: "Adds the runs you ticked",
      icon: Table,
      needs: null,
    },
    {
      id: "tile",
      label: "A tile on screen",
      note: "Use the message icon on any tile",
      icon: LayoutPanelTop,
      needs: null,
    },
    {
      id: "repo",
      label: "Code folder",
      note: "A repo Claude Code or Codex wrote",
      icon: FolderGit2,
      needs: "needs daemon",
    },
    {
      id: "dataset",
      label: "Upload a dataset",
      note: "CSV, Excel or Parquet",
      icon: Database,
      needs: "needs daemon",
    },
  ],
};

export const LAB_SESSIONS = [
  { id: "s1", title: "Sweep the majors on H1 and H4", when: "Today" },
  { id: "s2", title: "Why does ETH M15 beat H1?", when: "Today" },
  { id: "s3", title: "Import the vol forecaster", when: "Yesterday" },
  { id: "s4", title: "Leakage check on session flags", when: "Sep 29" },
];
