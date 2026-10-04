/** Panels Home offers. Pods and News come straight from Portfolio, so they stay one panel, not two. */
import type { Component } from "svelte";
import Inbox from "@lucide/svelte/icons/inbox";
import Activity from "@lucide/svelte/icons/activity";
import ChartLine from "@lucide/svelte/icons/chart-line";
import ScanSearch from "@lucide/svelte/icons/scan-search";
import CalendarDays from "@lucide/svelte/icons/calendar-days";
import History from "@lucide/svelte/icons/history";
import Pin from "@lucide/svelte/icons/pin";
import { PORTFOLIO_PANELS } from "$lib/portfolio/catalog";
import PinnedPanel from "$lib/lab/panels/PinnedPanel.svelte";
import NeedsPanel from "./panels/NeedsPanel.svelte";
import GoingPanel from "./panels/GoingPanel.svelte";
import MarketsPanel from "./panels/MarketsPanel.svelte";
import ScreenerPanel from "./panels/ScreenerPanel.svelte";
import CalendarPanel from "./panels/CalendarPanel.svelte";
import RecentPanel from "./panels/RecentPanel.svelte";

export type HomePanel = {
  title: string;
  icon: Component;
  note: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  view: Component<any>;
};

export const HOME_PANELS: Record<string, HomePanel> = {
  needs: {
    title: "Needs you",
    icon: Inbox,
    note: "Everything waiting on you",
    view: NeedsPanel,
  },
  going: {
    title: "Going on",
    icon: Activity,
    note: "Running sessions and jobs",
    view: GoingPanel,
  },
  pods: {
    ...PORTFOLIO_PANELS.pods,
    title: "Pods",
    note: "Live and paper, at a glance",
  },
  events: PORTFOLIO_PANELS.events,
  markets: {
    title: "Markets",
    icon: ChartLine,
    note: "Your watchlist",
    view: MarketsPanel,
  },
  screener: {
    title: "Screener",
    icon: ScanSearch,
    note: "Built by the copilot from a description",
    view: ScreenerPanel,
  },
  calendar: {
    title: "Coming up",
    icon: CalendarDays,
    note: "Events that move prices",
    view: CalendarPanel,
  },
  recent: {
    title: "Recent",
    icon: History,
    note: "Library items you touched",
    view: RecentPanel,
  },
  pinned: {
    title: "Pinned by the copilot",
    icon: Pin,
    note: "A panel the copilot built",
    view: PinnedPanel,
  },
};
