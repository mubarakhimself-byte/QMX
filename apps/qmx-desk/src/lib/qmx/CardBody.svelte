<script lang="ts">
  import { things } from "$lib/shell/things.svelte";
  import Waiting from "./cards/Waiting.svelte";
  import Since from "./cards/Since.svelte";
  import Units from "./cards/Units.svelte";
  import Pods from "./cards/Pods.svelte";
  import Running from "./cards/Running.svelte";
  import Markets from "./cards/Markets.svelte";
  import Positions from "./cards/Positions.svelte";
  import Nodes from "./cards/Nodes.svelte";
  import Readings from "./cards/Readings.svelte";
  import Spark from "./Spark.svelte";
  import Stats from "./Stats.svelte";
  import { shell } from "$lib/shell/state.svelte";

  // What a card widget shows. Each card reads its size mode from the frame
  // around it (tiles/panel-size.ts) and defines compact, regular and
  // expanded; every row is one of his things and opens its page.
  let { id }: { id: string } = $props();
  const unit = $derived(id.startsWith("t:") ? things.get(id.slice(2)) : undefined);
</script>

{#if id === "waiting"}<Waiting />
{:else if id === "since"}<Since />
{:else if id === "units"}<Units />
{:else if id === "pods"}<Pods />
{:else if id === "running"}<Running />
{:else if id === "markets"}<Markets />
{:else if id === "positions"}<Positions />
{:else if id === "nodes"}<Nodes />
{:else if id === "g:readings"}<Readings />
{:else if unit}
  {@const s = unit.sections?.find((x) => x.id === "results")}
  {@const n = unit.sections?.find((x) => x.id === "numbers")}
  <!-- A unit on a trading board: its curve and two numbers; the title opens its page. (Trading is not redesigned yet.) -->
  <button class="flex h-full min-h-0 w-full flex-col rounded-md text-left transition-colors duration-150 hover:bg-white/[0.03]" title="Open {unit.name}" onclick={() => shell.open({ id: unit.id })}>
    {#if s && s.body.t === "spark"}
      <div class="min-h-[6rem] w-full flex-1" style:--line="var(--{unit.tone === 'live' ? 'live' : 'paper'})"><Spark series={s.body.series} note={s.body.note} /></div>
    {/if}
    {#if n && n.body.t === "stats"}
      <div class="w-full shrink-0 [&_dd]:text-xl"><Stats stats={n.body.stats.slice(0, 2)} /></div>
    {/if}
  </button>
{:else}
  <p class="text-muted-foreground p-2.5" data-empty>This card has nothing to show.</p>
{/if}
