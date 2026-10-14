<script lang="ts">
  /**
   * MIS: the trading servers' market labelers (regime, volatility, liquidity,
   * news state) and who listens to them (pod guards and the kill switch,
   * never bots). Shadow labelers are watched, not obeyed, until you promote
   * them; promote and demote work in the browser (demo). A big revamp is
   * coming (operator, 2026-10-03); this is the placeholder shape.
   */
  import Radar from "@lucide/svelte/icons/radar";
  import { Switch } from "$lib/components/ui/switch";
  import { cn } from "$lib/utils";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { workbench } from "$lib/workbench/workbench.svelte";

  const size = panelSize();
  let labelers = $state([
    {
      name: "Volatility state",
      value: "elevated",
      since: "09:10",
      lane: "live",
      feeds: "Pod guards, kill switch",
    },
    {
      name: "Session",
      value: "London–NY overlap",
      since: "12:00",
      lane: "live",
      feeds: "Pod guards",
    },
    {
      name: "News state",
      value: "CPI window in 2h",
      since: "—",
      lane: "live",
      feeds: "Protection windows",
    },
    {
      name: "Regime (HMM)",
      value: "trending",
      since: "yesterday",
      lane: "shadow",
      feeds: "Pod guards once promoted",
    },
    {
      name: "Liquidity (crypto)",
      value: "thin weekend book",
      since: "Sat",
      lane: "shadow",
      feeds: "Pod guards once promoted",
    },
  ]);
  const live = $derived(labelers.filter((l) => l.lane === "live").length);

  function flip(name: string) {
    const l = labelers.find((x) => x.name === name)!;
    l.lane = l.lane === "live" ? "shadow" : "live";
    workbench.notify(
      `${l.name} is ${l.lane === "live" ? "promoted: pod guards listen to it" : "back in shadow: watched, not obeyed"}.`,
    );
  }
</script>

{#if size.mode === "compact"}
  <PanelSummary
    label="Market labelers"
    value={`${live} live`}
    status={`${labelers.length - live} in shadow`}
  />
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-2">
      <span class="text-muted-foreground text-xs"
        >{live} live · {labelers.length - live} shadow</span
      >
      <InfoTip
        class="ml-auto"
        label="Explain MIS"
        text="Labels the trading servers put on the market. Pod guards and the kill switch listen to live ones; bots never do. Shadow labelers are watched, not obeyed, until you promote them. MIS is being redesigned; build new labelers in the Lab."
      />
    </div>
    <ul class="min-h-0 flex-1 overflow-auto">
      {#each labelers as l (l.name)}
        <li
          class="border-border/50 px-panel py-row flex items-center gap-3 border-b"
          title={`Feeds: ${l.feeds}`}
        >
          <Radar
            class={cn(
              "size-4 shrink-0",
              l.lane === "live" ? "text-primary" : "text-muted-foreground",
            )}
          />
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm">
              <span class="font-medium">{l.name}</span>
              <span class="text-muted-foreground text-xs">since {l.since}</span>
            </p>
            {#if size.mode === "expanded"}
              <p class="text-muted-foreground truncate text-xs">
                Feeds: {l.feeds}
              </p>
            {/if}
          </div>
          <span class="shrink-0 rounded-md border px-2 py-0.5 text-xs"
            >{l.value}</span
          >
          <label class="flex w-20 shrink-0 items-center justify-end gap-2">
            <span
              class={cn(
                "text-xs",
                l.lane === "live" ? "text-success" : "text-muted-foreground",
              )}>{l.lane === "live" ? "Live" : "Shadow"}</span
            >
            <Switch
              checked={l.lane === "live"}
              onCheckedChange={() => flip(l.name)}
              aria-label={`${l.name} live`}
            />
          </label>
        </li>
      {/each}
    </ul>
  </div>
{/if}
