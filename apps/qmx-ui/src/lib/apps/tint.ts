import type { Group } from "./apps.svelte";

/** Icon tile colour per group, so a group reads at a glance. */
export const GROUP_TINT: Record<Group, string> = {
  markets: "bg-chart-1/15 text-chart-1",
  watching: "bg-chart-2/15 text-chart-2",
  research: "bg-chart-3/15 text-chart-3",
  helpers: "bg-chart-4/15 text-chart-4",
};
