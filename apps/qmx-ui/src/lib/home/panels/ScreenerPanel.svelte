<script lang="ts">
  /**
   * A coin screener that is itself a panel description (mini-app SDK tier
   * 1): the copilot built it and can change its columns or filters by
   * rewriting the description; QMX draws it. Sample values.
   */
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import SpecView from "$lib/sdk/SpecView.svelte";
  import type { PanelSpec } from "$lib/sdk/spec";
  import { workbench } from "$lib/workbench/workbench.svelte";

  const SPEC: PanelSpec = {
    title: "Momentum screener",
    description:
      "Top coins by 7-day momentum, with volume, funding and news mood.",
    data: "screener.momentum",
    root: "page",
    elements: {
      page: { type: "Stack", children: ["table", "note"] },
      table: {
        type: "Table",
        props: {
          columns: [
            "Coin",
            "7-day momentum",
            "Volume vs usual",
            "Funding",
            "News mood",
          ],
          rows: [
            ["LINK", "+14.2%", "1.9×", "+0.011%", "Positive"],
            ["SOL", "+9.8%", "1.4×", "+0.024%", "Mixed"],
            ["AVAX", "+6.1%", "1.2×", "+0.008%", "Positive"],
            ["ETH", "+4.4%", "1.1×", "+0.010%", "Positive"],
            ["BTC", "+2.9%", "0.9×", "+0.006%", "Neutral"],
            ["DOGE", "−3.5%", "0.7×", "−0.004%", "Negative"],
          ],
        },
      },
      note: {
        type: "Callout",
        props: {
          tone: "info",
          text: "Built by the copilot from a description. Ask it to change the columns or filters.",
        },
      },
    },
  };

  /* eslint-disable svelte/no-navigation-without-resolve */
  function change() {
    goto(
      `${resolve("/copilot")}?ask=${encodeURIComponent("Change the momentum screener on Home: ")}`,
    );
  } /* eslint-enable svelte/no-navigation-without-resolve */
</script>

<div class="flex h-full flex-col">
  <div class="min-h-0 flex-1 overflow-auto p-3">
    <SpecView
      spec={SPEC}
      onaction={(op) => workbench.notify(`Asked the host to run ${op}.`)}
    />
  </div>
  <div class="flex shrink-0 justify-end border-t px-3 py-1.5">
    <Button size="sm" variant="ghost" onclick={change}
      ><Sparkles />Change with the copilot</Button
    >
  </div>
</div>
