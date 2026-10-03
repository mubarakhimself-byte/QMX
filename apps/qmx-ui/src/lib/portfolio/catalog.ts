/** Panels the Portfolio offers; apps can add more later. */
import type { Component } from "svelte";
import Building2 from "@lucide/svelte/icons/building-2";
import Gauge from "@lucide/svelte/icons/gauge";
import BookOpen from "@lucide/svelte/icons/book-open";
import ListChecks from "@lucide/svelte/icons/list-checks";
import PieChart from "@lucide/svelte/icons/chart-pie";
import Newspaper from "@lucide/svelte/icons/newspaper";
import LayoutGrid from "@lucide/svelte/icons/layout-grid";
import CandlestickChart from "@lucide/svelte/icons/chart-candlestick";
import ShieldAlert from "@lucide/svelte/icons/shield-alert";
import Table from "@lucide/svelte/icons/table";
import Server from "@lucide/svelte/icons/server";
import Route from "@lucide/svelte/icons/route";
import PenLine from "@lucide/svelte/icons/pen-line";
import Inbox from "@lucide/svelte/icons/inbox";
import Scale from "@lucide/svelte/icons/scale";
import Grid3x3 from "@lucide/svelte/icons/grid-3x3";
import Radar from "@lucide/svelte/icons/radar";
import AccountsPanel from "./panels/AccountsPanel.svelte";
import RiskPanel from "./panels/RiskPanel.svelte";
import BookPanel from "./panels/BookPanel.svelte";
import RulesPanel from "./panels/RulesPanel.svelte";
import ExposurePanel from "./panels/ExposurePanel.svelte";
import NewsPanel from "./panels/NewsPanel.svelte";
import WallPanel from "./panels/WallPanel.svelte";
import ChartPanel from "./panels/ChartPanel.svelte";
import ControlPanel from "./panels/ControlPanel.svelte";
import PositionsPanel from "./panels/PositionsPanel.svelte";
import NodesPanel from "./panels/NodesPanel.svelte";
import PromotionsPanel from "./panels/PromotionsPanel.svelte";
import SigningPanel from "./panels/SigningPanel.svelte";
import ApprovalsPanel from "./panels/ApprovalsPanel.svelte";
import AllocatePanel from "./panels/AllocatePanel.svelte";
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
    note: "Exchanges, brokers, accounts and their Books",
    view: AccountsPanel,
  },
  risk: {
    title: "Risk",
    icon: Gauge,
    note: "Every Book: budget, kill line, kill switch",
    view: RiskPanel,
  },
  book: {
    title: "Book",
    icon: BookOpen,
    note: "Risk source, sizing ladder, seats",
    view: BookPanel,
  },
  rules: {
    title: "Rules",
    icon: ListChecks,
    note: "Limits: OK, near or tripped",
    view: RulesPanel,
  },
  exposure: {
    title: "Exposure",
    icon: PieChart,
    note: "By asset across accounts",
    view: ExposurePanel,
  },
  news: {
    title: "Events",
    icon: Newspaper,
    note: "What's coming and which Books it hits",
    view: NewsPanel,
  },
  wall: {
    title: "Books",
    icon: LayoutGrid,
    note: "A tile per Book",
    view: WallPanel,
    trading: true,
  },
  chart: {
    title: "Chart",
    icon: CandlestickChart,
    note: "Held markets with entries",
    view: ChartPanel,
    trading: true,
  },
  control: {
    title: "Kill switch",
    icon: ShieldAlert,
    note: "Levels and your powers",
    view: ControlPanel,
    trading: true,
  },
  positions: {
    title: "Positions",
    icon: Table,
    note: "Open positions and orders, live",
    view: PositionsPanel,
    trading: true,
  },
  nodes: {
    title: "Trading servers",
    icon: Server,
    note: "Where trading runs",
    view: NodesPanel,
    trading: true,
  },
  promotions: {
    title: "Road to live",
    icon: Route,
    note: "Research-paper, node-paper, live",
    view: PromotionsPanel,
  },
  signing: {
    title: "Promotion card",
    icon: PenLine,
    note: "Checks, evidence, signature",
    view: SigningPanel,
  },
  approvals: {
    title: "Agent requests",
    icon: Inbox,
    note: "Approve or decline what agents ask",
    view: ApprovalsPanel,
  },
  allocate: {
    title: "Allocate",
    icon: Scale,
    note: "What-if allocation across Books",
    view: AllocatePanel,
  },
  correlation: {
    title: "Correlation",
    icon: Grid3x3,
    note: "How Books move together",
    view: CorrelationPanel,
  },
  mis: {
    title: "MIS",
    icon: Radar,
    note: "Market labelers and who listens",
    view: MisPanel,
  },
};
