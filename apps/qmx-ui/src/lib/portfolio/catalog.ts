/** Panels the Portfolio offers; apps can add more later. */
import type { Component } from "svelte";
import Building2 from "@lucide/svelte/icons/building-2";
import Boxes from "@lucide/svelte/icons/boxes";
import SlidersHorizontal from "@lucide/svelte/icons/sliders-horizontal";
import PieChart from "@lucide/svelte/icons/chart-pie";
import Newspaper from "@lucide/svelte/icons/newspaper";
import CandlestickChart from "@lucide/svelte/icons/chart-candlestick";
import ShieldAlert from "@lucide/svelte/icons/shield-alert";
import Table from "@lucide/svelte/icons/table";
import Server from "@lucide/svelte/icons/server";
import Route from "@lucide/svelte/icons/route";
import PenLine from "@lucide/svelte/icons/pen-line";
import NotebookPen from "@lucide/svelte/icons/notebook-pen";
import Grid3x3 from "@lucide/svelte/icons/grid-3x3";
import Radar from "@lucide/svelte/icons/radar";
import AccountsPanel from "./panels/AccountsPanel.svelte";
import PodsPanel from "./panels/PodsPanel.svelte";
import PodPanel from "./panels/PodPanel.svelte";
import ExposurePanel from "./panels/ExposurePanel.svelte";
import EventsPanel from "./panels/EventsPanel.svelte";
import BotChartsPanel from "./panels/BotChartsPanel.svelte";
import ControlPanel from "./panels/ControlPanel.svelte";
import PositionsPanel from "./panels/PositionsPanel.svelte";
import HoldingsPanel from "./panels/HoldingsPanel.svelte";
import Layers from "@lucide/svelte/icons/layers";
import NodesPanel from "./panels/NodesPanel.svelte";
import RoadPanel from "./panels/RoadPanel.svelte";
import SigningPanel from "./panels/SigningPanel.svelte";
import JournalPanel from "./panels/JournalPanel.svelte";
import CorrelationPanel from "./panels/CorrelationPanel.svelte";
import MisPanel from "./panels/MisPanel.svelte";

export type PortfolioPanel = {
  title: string;
  icon: Component;
  note: string;
  view: Component;
  /** Shows live or paper work: its border takes the paper/live colour. */
  trading?: boolean;
};

export const PORTFOLIO_PANELS: Record<string, PortfolioPanel> = {
  accounts: {
    title: "Accounts",
    icon: Building2,
    note: "Exchanges, spot accounts and their pods",
    view: AccountsPanel,
  },
  pods: {
    title: "Pods",
    icon: Boxes,
    note: "Every pod as a card",
    view: PodsPanel,
    trading: true,
  },
  pod: {
    title: "Pod",
    icon: SlidersHorizontal,
    note: "Adjust one pod: limits, weights, method",
    view: PodPanel,
  },
  events: {
    title: "News and events",
    icon: Newspaper,
    note: "Crypto and FX, with sentiment and source",
    view: EventsPanel,
  },
  exposure: {
    title: "Exposure",
    icon: PieChart,
    note: "What you hold, by coin",
    view: ExposurePanel,
  },
  botcharts: {
    title: "Bots trading",
    icon: CandlestickChart,
    note: "A chart per trading bot",
    view: BotChartsPanel,
  },
  holdings: {
    title: "Holdings",
    icon: Layers,
    note: "Positions, exposure and correlation as tabs",
    view: HoldingsPanel,
    trading: true,
  },
  positions: {
    title: "Positions",
    icon: Table,
    note: "Sort, group and filter what's open",
    view: PositionsPanel,
    trading: true,
  },
  control: {
    title: "Kill switch",
    icon: ShieldAlert,
    note: "Levels and your powers",
    view: ControlPanel,
    trading: true,
  },
  correlation: {
    title: "Correlation",
    icon: Grid3x3,
    note: "How pods move together",
    view: CorrelationPanel,
  },
  nodes: {
    title: "Trading servers",
    icon: Server,
    note: "Latency, health and actions",
    view: NodesPanel,
    trading: true,
  },
  road: {
    title: "Road to live",
    icon: Route,
    note: "On paper, ready, first live days",
    view: RoadPanel,
  },
  signing: {
    title: "Promotion card",
    icon: PenLine,
    note: "What you sign and its checks",
    view: SigningPanel,
  },
  journal: {
    title: "Trading journal",
    icon: NotebookPen,
    note: "A bot's trades, events and your notes",
    view: JournalPanel,
  },
  mis: {
    title: "MIS",
    icon: Radar,
    note: "Market labelers and who listens",
    view: MisPanel,
  },
};
