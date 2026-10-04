/**
 * Panels the Lab offers. Apps can contribute more later (canvas-widget slot);
 * a stored layout naming a panel nobody provides shows a reason instead.
 */
import type { Component } from "svelte";
import Boxes from "@lucide/svelte/icons/boxes";
import Workflow from "@lucide/svelte/icons/workflow";
import SlidersHorizontal from "@lucide/svelte/icons/sliders-horizontal";
import Table from "@lucide/svelte/icons/table";
import Grid3x3 from "@lucide/svelte/icons/grid-3x3";
import ChartLine from "@lucide/svelte/icons/chart-line";
import ShieldCheck from "@lucide/svelte/icons/shield-check";
import Columns3 from "@lucide/svelte/icons/columns-3";
import BrainCircuit from "@lucide/svelte/icons/brain-circuit";
import Plug from "@lucide/svelte/icons/plug";
import Database from "@lucide/svelte/icons/database";
import Cpu from "@lucide/svelte/icons/cpu";
import Bot from "@lucide/svelte/icons/bot";
import ScrollText from "@lucide/svelte/icons/scroll-text";
import AssetsPanel from "./panels/AssetsPanel.svelte";
import EditorPanel from "./panels/EditorPanel.svelte";
import InspectorPanel from "./panels/InspectorPanel.svelte";
import RunsPanel from "./panels/RunsPanel.svelte";
import MatrixPanel from "./panels/MatrixPanel.svelte";
import EquityPanel from "./panels/EquityPanel.svelte";
import RobustnessPanel from "./panels/RobustnessPanel.svelte";
import ComparePanel from "./panels/ComparePanel.svelte";
import TrainingPanel from "./panels/TrainingPanel.svelte";
import SlotsPanel from "./panels/SlotsPanel.svelte";
import DataPanel from "./panels/DataPanel.svelte";
import ComputePanel from "./panels/ComputePanel.svelte";
import AgentsPanel from "./panels/AgentsPanel.svelte";
import LogsPanel from "./panels/LogsPanel.svelte";
import ResourcesPanel from "./panels/ResourcesPanel.svelte";
import PodStackPanel from "./panels/PodStackPanel.svelte";
import BlockPanel from "./panels/BlockPanel.svelte";
import SizeTrailPanel from "./panels/SizeTrailPanel.svelte";
import FanPanel from "./panels/FanPanel.svelte";
import StressPanel from "./panels/StressPanel.svelte";
import InterventionsPanel from "./panels/InterventionsPanel.svelte";
import PodEquityPanel from "./panels/PodEquityPanel.svelte";
import PodResourcesPanel from "./panels/PodResourcesPanel.svelte";
import HeadToHeadPanel from "./panels/HeadToHeadPanel.svelte";
import PaperRunPanel from "./panels/PaperRunPanel.svelte";
import PaperFeedPanel from "./panels/PaperFeedPanel.svelte";
import GraduatePanel from "./panels/GraduatePanel.svelte";
import Boxes2 from "@lucide/svelte/icons/layers-2";
import Puzzle from "@lucide/svelte/icons/puzzle";
import ChartBarDecreasing from "@lucide/svelte/icons/chart-bar-decreasing";
import ChartArea from "@lucide/svelte/icons/chart-area";
import Siren from "@lucide/svelte/icons/siren";
import History from "@lucide/svelte/icons/history";
import Swords from "@lucide/svelte/icons/swords";
import Wallet from "@lucide/svelte/icons/wallet";
import Radio from "@lucide/svelte/icons/radio";
import Rocket from "@lucide/svelte/icons/rocket";
import Pin from "@lucide/svelte/icons/pin";
import PinnedPanel from "./panels/PinnedPanel.svelte";

import Layers from "@lucide/svelte/icons/layers";

export type LabPanel = {
  title: string;
  icon: Component;
  note: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  view: Component<any>;
};

export const LAB_PANELS: Record<string, LabPanel> = {
  resources: {
    title: "Resources",
    icon: Layers,
    note: "Items, data, machines and slots",
    view: ResourcesPanel,
  },
  assets: {
    title: "Toolbox",
    icon: Boxes,
    note: "Workflows, bots, models, data, tests",
    view: AssetsPanel,
  },
  editor: {
    title: "Editor",
    icon: Workflow,
    note: "Graph, code or import",
    view: EditorPanel,
  },
  inspector: {
    title: "Inspector",
    icon: SlidersHorizontal,
    note: "Settings and code of a step",
    view: InspectorPanel,
  },
  runs: {
    title: "Runs",
    icon: Table,
    note: "Every run, sortable, tick to compare",
    view: RunsPanel,
  },
  matrix: {
    title: "Sweep grid",
    icon: Grid3x3,
    note: "Markets × timeframes",
    view: MatrixPanel,
  },
  equity: {
    title: "Equity",
    icon: ChartLine,
    note: "Selected run with ticked overlays",
    view: EquityPanel,
  },
  robustness: {
    title: "Robustness",
    icon: ShieldCheck,
    note: "Checks, cheapest first",
    view: RobustnessPanel,
  },
  compare: {
    title: "Compare",
    icon: Columns3,
    note: "Ticked runs side by side",
    view: ComparePanel,
  },
  training: {
    title: "Training",
    icon: BrainCircuit,
    note: "Pipeline, curves and split",
    view: TrainingPanel,
  },
  slots: {
    title: "Model slots",
    icon: Plug,
    note: "Where models plug in",
    view: SlotsPanel,
  },
  data: {
    title: "Data",
    icon: Database,
    note: "Datasets and features",
    view: DataPanel,
  },
  compute: {
    title: "Compute",
    icon: Cpu,
    note: "Where work runs",
    view: ComputePanel,
  },
  agents: {
    title: "Agents",
    icon: Bot,
    note: "Agents and sub-agents",
    view: AgentsPanel,
  },
  podstack: {
    title: "Pod",
    icon: Boxes2,
    note: "A pod's blocks, slot by slot",
    view: PodStackPanel,
  },
  block: {
    title: "Block",
    icon: Puzzle,
    note: "The selected block's settings",
    view: BlockPanel,
  },
  sizetrail: {
    title: "Size trail",
    icon: ChartBarDecreasing,
    note: "Why a trade got its size",
    view: SizeTrailPanel,
  },
  fan: {
    title: "Drawdown fan",
    icon: ChartArea,
    note: "Chance of the kill line, per pod",
    view: FanPanel,
  },
  stress: {
    title: "Stress board",
    icon: Siren,
    note: "Crises × pods",
    view: StressPanel,
  },
  interventions: {
    title: "Interventions",
    icon: History,
    note: "Every shrink, refusal and halt",
    view: InterventionsPanel,
  },
  podequity: {
    title: "Pod equity",
    icon: ChartLine,
    note: "Ticked pods on the same bots",
    view: PodEquityPanel,
  },
  podres: {
    title: "Pod resources",
    icon: Wallet,
    note: "Pods, bots, blocks, stress and paper money",
    view: PodResourcesPanel,
  },
  headtohead: {
    title: "Head to head",
    icon: Swords,
    note: "Ticked pods as cards, side by side",
    view: HeadToHeadPanel,
  },
  paperrun: {
    title: "Paper run",
    icon: Radio,
    note: "A pod on paper against its own test",
    view: PaperRunPanel,
  },
  paperfeed: {
    title: "Live decisions",
    icon: History,
    note: "Each paper trade and how it was sized",
    view: PaperFeedPanel,
  },
  graduate: {
    title: "Ready for live?",
    icon: Rocket,
    note: "Checks before promotion",
    view: GraduatePanel,
  },
  logs: {
    title: "Log",
    icon: ScrollText,
    note: "Output of the selected run",
    view: LogsPanel,
  },
  pinned: {
    title: "Pinned by the copilot",
    icon: Pin,
    note: "A panel the copilot built from a description",
    view: PinnedPanel,
  },
};
