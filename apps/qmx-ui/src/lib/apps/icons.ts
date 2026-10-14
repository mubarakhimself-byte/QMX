import type { Component } from "svelte";
import Activity from "@lucide/svelte/icons/activity";
import Binoculars from "@lucide/svelte/icons/binoculars";
import Calculator from "@lucide/svelte/icons/calculator";
import CalendarClock from "@lucide/svelte/icons/calendar-clock";
import Coins from "@lucide/svelte/icons/coins";
import FileText from "@lucide/svelte/icons/file-text";
import Gauge from "@lucide/svelte/icons/gauge";
import LayoutGrid from "@lucide/svelte/icons/layout-grid";
import Network from "@lucide/svelte/icons/network";
import Newspaper from "@lucide/svelte/icons/newspaper";
import Percent from "@lucide/svelte/icons/percent";
import PiggyBank from "@lucide/svelte/icons/piggy-bank";
import ScanSearch from "@lucide/svelte/icons/scan-search";
import ServerCog from "@lucide/svelte/icons/server-cog";
import Telescope from "@lucide/svelte/icons/telescope";
import TrendingUp from "@lucide/svelte/icons/trending-up";
import type { IconName } from "./apps.svelte";

export const ICONS: Record<IconName, Component> = {
  activity: Activity,
  binoculars: Binoculars,
  calculator: Calculator,
  "calendar-clock": CalendarClock,
  coins: Coins,
  "file-text": FileText,
  gauge: Gauge,
  "layout-grid": LayoutGrid,
  network: Network,
  newspaper: Newspaper,
  percent: Percent,
  "piggy-bank": PiggyBank,
  "scan-search": ScanSearch,
  "server-cog": ServerCog,
  telescope: Telescope,
  "trending-up": TrendingUp,
};
