<script lang="ts">
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";
  import PanelRight from "@lucide/svelte/icons/panel-right";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import * as Resizable from "$lib/components/ui/resizable";
  import * as Tabs from "$lib/components/ui/tabs";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import WidgetFrame, {
    type WidgetState,
  } from "$lib/workbench/WidgetFrame.svelte";
  import Composer from "$lib/workbench/Composer.svelte";

  // Design-review gallery: a sample mini-app shape. Not an installed app, no live data.
  const NAV = ["Overview", "Signals", "Risk"];
  let navTab = $state("Overview");
  let copilotOpen = $state(true);
  let expanded = $state<string | null>(null);

  const SAMPLE_ROWS = [
    ["Sample A", "1.000", "+0.4%"],
    ["Sample B", "2.000", "−1.2%"],
    ["Sample C", "3.000", "+2.1%"],
    ["Sample D", "4.000", "−0.3%"],
  ];
  const SPARK = [8, 9, 7, 10, 12, 11, 13, 12, 15, 14, 16, 18, 17, 19];

  const STATES: { title: string; state: WidgetState; reason?: string }[] = [
    { title: "Loading widget", state: "loading" },
    {
      title: "Empty widget",
      state: "empty",
      reason: "No rows match this filter.",
    },
    {
      title: "Unavailable widget",
      state: "unavailable",
      reason: "Market data provider is not configured.",
    },
    {
      title: "Failed widget",
      state: "failed",
      reason: "Query refused: instrument not found.",
    },
    {
      title: "Stale widget",
      state: "stale",
      reason: "Snapshot from 14:02. Live feed paused.",
    },
    { title: "Reconnecting widget", state: "reconnecting" },
  ];

  const sparkPath = $derived.by(() => {
    const max = Math.max(...SPARK);
    const min = Math.min(...SPARK);
    return SPARK.map(
      (v, i) =>
        `${i === 0 ? "M" : "L"}${(i / (SPARK.length - 1)) * 100},${40 - ((v - min) / (max - min)) * 36 - 2}`,
    ).join(" ");
  });
</script>

{#snippet table()}
  <table class="tabular w-full text-sm">
    <thead class="text-muted-foreground text-left text-xs">
      <tr
        ><th class="py-1.5 font-medium">Item</th><th class="font-medium"
          >Value</th
        ><th class="text-right font-medium">Change</th></tr
      >
    </thead>
    <tbody>
      {#each SAMPLE_ROWS as [name, value, change] (name)}
        <tr class="border-t">
          <td class="py-1.5">{name}</td>
          <td>{value}</td>
          <td
            class="text-right {change.startsWith('+')
              ? 'text-success'
              : 'text-destructive'}"
          >
            {change.startsWith("+") ? "▲" : "▼"}
            {change}
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
{/snippet}

{#snippet chart()}
  <div class="flex items-end gap-4">
    <div>
      <p class="text-muted-foreground text-xs">Sample value</p>
      <p class="tabular text-xl font-semibold">19.00</p>
      <p class="text-success text-xs">▲ +1.00 (+5.6%)</p>
    </div>
    <svg
      viewBox="0 0 100 40"
      preserveAspectRatio="none"
      class="text-chart-1 h-16 flex-1"
      aria-hidden="true"
    >
      <path
        d={sparkPath}
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        vector-effect="non-scaling-stroke"
      />
    </svg>
  </div>
{/snippet}

<svelte:head><title>Component gallery · QMX</title></svelte:head>

<div class="flex h-full flex-col">
  <div
    class="bg-warning/15 text-foreground flex h-8 shrink-0 items-center gap-2 px-4 text-xs"
  >
    <FlaskConical class="text-warning size-3.5" />
    Component gallery. Sample layout and sample numbers, not an installed app and
    not market data.
  </div>

  <!-- Pack-declared app navigation (nav[]); omitted when a pack declares none. -->
  <header class="flex h-11 shrink-0 items-center gap-3 border-b px-3">
    <span class="text-sm font-semibold">Sample research app</span>
    <Tabs.Root bind:value={navTab}>
      <Tabs.List variant="line">
        {#each NAV as n (n)}<Tabs.Trigger value={n}>{n}</Tabs.Trigger>{/each}
      </Tabs.List>
    </Tabs.Root>
    <Button
      variant="ghost"
      size="icon-sm"
      class="ml-auto"
      aria-label="Toggle app copilot"
      aria-pressed={copilotOpen}
      onclick={() => (copilotOpen = !copilotOpen)}
    >
      <PanelRight />
    </Button>
  </header>

  <Resizable.PaneGroup direction="horizontal" class="min-h-0 flex-1">
    <Resizable.Pane defaultSize={72} minSize={45}>
      <div class="h-full overflow-auto p-3">
        {#if expanded}
          <!-- Expand is a layout change with an explicit return, not a new destination. -->
          <div class="flex h-full flex-col gap-2">
            <Button
              variant="ghost"
              size="sm"
              class="self-start"
              onclick={() => (expanded = null)}
            >
              <ArrowLeft /> Back to {navTab}
            </Button>
            <WidgetFrame
              title={expanded}
              class="flex-1"
              onclose={() => (expanded = null)}
            >
              {@render chart()}
              <div class="mt-4">{@render table()}</div>
            </WidgetFrame>
          </div>
        {:else}
          <div
            class="grid auto-rows-[minmax(11rem,auto)] gap-3 md:grid-cols-2 xl:grid-cols-3"
          >
            <WidgetFrame
              title="Price summary"
              class="xl:col-span-2"
              onexpand={() => (expanded = "Price summary")}
            >
              {#snippet controls()}<Badge variant="secondary">SAMPLE</Badge
                >{/snippet}
              {@render chart()}
            </WidgetFrame>
            <WidgetFrame
              title="Key figures"
              onexpand={() => (expanded = "Key figures")}
            >
              {@render table()}
            </WidgetFrame>
            {#each STATES as s (s.title)}
              <WidgetFrame title={s.title} state={s.state} reason={s.reason}>
                {@render table()}
              </WidgetFrame>
            {/each}
          </div>
        {/if}
      </div>
    </Resizable.Pane>
    {#if copilotOpen}
      <Resizable.Handle />
      <Resizable.Pane defaultSize={28} minSize={20}>
        <aside aria-label="App copilot" class="bg-panel flex h-full flex-col">
          <div
            class="flex h-10 shrink-0 items-center border-b px-3 text-sm font-medium"
          >
            App copilot
            <Badge variant="outline" class="ml-2">app-use</Badge>
          </div>
          <div class="text-muted-foreground min-h-0 flex-1 p-3 text-xs">
            Shown only for apps that declare a copilot profile. Its history is
            separate from the main Copilot.
          </div>
          <div class="p-3"><Composer placeholder="Ask about this app…" /></div>
        </aside>
      </Resizable.Pane>
    {/if}
  </Resizable.PaneGroup>
</div>
