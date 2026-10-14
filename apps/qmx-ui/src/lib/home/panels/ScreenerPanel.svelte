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
  import InfoTip from "$lib/workbench/InfoTip.svelte";

  const SPEC: PanelSpec = {
    title: "Momentum screener",
    description:
      "Top coins by 7-day momentum, with volume, funding and news mood.",
    data: "screener.momentum",
    root: "page",
    elements: {
      page: { type: "Stack", children: ["table"] },
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
  <div class="px-panel flex h-10 shrink-0 items-center gap-2">
    <span class="truncate text-sm font-medium">{SPEC.title}</span>
    <InfoTip
      label="Explain the screener"
      text="The copilot built this from a description: top coins by 7-day momentum, with volume, funding and news mood. Ask it to change the columns or filters."
    />
    <Button size="sm" variant="ghost" class="ml-auto h-7" onclick={change}
      ><Sparkles />Change</Button
    >
  </div>
  <div class="px-panel pb-panel min-h-0 flex-1 overflow-auto">
    <SpecView
      spec={SPEC}
      onaction={(op) => workbench.notify(`Asked the host to run ${op}.`)}
    />
  </div>
</div>
