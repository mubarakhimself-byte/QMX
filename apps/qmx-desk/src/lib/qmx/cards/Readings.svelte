<script lang="ts">
  import Stats from "../Stats.svelte";
  import Fit from "../Fit.svelte";
  import { panelSize } from "../tiles/panel-size";

  // A mini app's card (Market intelligence): the regime per market. Compact:
  // the two markets that matter most. Regular and expanded: four numbers,
  // then a reading per market fills the rest.
  const size = panelSize();
  const top = [
    { label: "XAUUSD", value: "Trending" },
    { label: "EURUSD", value: "Choppy" },
    { label: "Spread", value: "Normal", tone: "up" as const },
    { label: "Fresh", value: "2m ago" },
  ];
  const per = [
    ["XAUUSD", "Trending", "1.18", "0.58"],
    ["EURUSD", "Choppy", "0.94", "0.47"],
    ["NAS100", "Trending", "1.09", "0.55"],
    ["BTCUSD", "Trending", "1.22", "0.61"],
    ["USDJPY", "Ranging", "0.97", "0.49"],
    ["USOIL", "Choppy", "0.91", "0.46"],
    ["XAGUSD", "Trending", "1.11", "0.56"],
    ["UK100", "Ranging", "0.99", "0.50"],
  ];
</script>

<div class="flex h-full min-h-0 flex-col">
  <div class="shrink-0"><Stats stats={size.mode === "compact" ? top.slice(0, 2) : top} /></div>
  <Fit items={per} title="Regime, variance ratio, Hurst" key={(r) => r[0]}>
    {#snippet row(r)}
      <div class="grid grid-cols-[5rem_minmax(0,1fr)_3.5rem_3.5rem] items-center gap-2 px-2.5 py-1 text-sm">
        <span class="num">{r[0]}</span><span class="truncate">{r[1]}</span><span class="num text-muted-foreground text-right">{r[2]}</span><span class="num text-muted-foreground text-right">{r[3]}</span>
      </div>
    {/snippet}
  </Fit>
</div>
