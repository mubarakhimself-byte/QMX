<script lang="ts">
  import { shell } from "./state.svelte";
  import * as Menu from "$lib/components/ui/dropdown-menu";
  import Icon from "$lib/qmx/Icon.svelte";
  import { cities } from "$lib/qmx/clock.svelte";
  import MarketClock from "./MarketClock.svelte";
  import { things } from "./things.svelte";

  // Always in view. Left: work (what runs, what waits for you, on which machines).
  // Middle: the markets' clocks. Right: trading, with its stop in three levels.
  const first = $derived(shell.fixture === "first");
  const worst = $derived(shell.fixture === "worst");
  const nf = new Intl.NumberFormat("en");

  // Stop levels, mildest first. A node is the app that trades; a machine is
  // where it runs. Pause keeps positions; stop ends a node; close flattens.
  type Level = "trading" | "paused" | "stopped" | "closed";
  let level = $state<Level>("trading");
  let armed = $state(false);
  const label: Record<Level, string> = {
    trading: "2 nodes trading",
    paused: "Paused: no new trades",
    stopped: "Nodes stopped",
    closed: "All closed and stopped",
  };
  const set = (l: Level) => ((level = l), (armed = false));
</script>

<footer class="sb border-border text-muted-foreground flex h-10 shrink-0 items-center gap-1 border-t px-2 text-sm">
  {#if !first}
    <button class="press h-7 shrink-0 gap-1.5 px-2 whitespace-nowrap" title="Open the runs" onclick={() => shell.go("runs")}>
      <span class="dot text-run size-1.5"></span><span class="num text-foreground">{nf.format(things.running.length)}</span> running
    </button>
    <button class="press h-7 shrink-0 gap-1.5 px-2 whitespace-nowrap" title="Open what is waiting for you" onclick={() => shell.go("needs")}>
      <span class="dot text-needs size-1.5"></span><span class="num text-foreground">{nf.format(things.needs.length)}</span> {things.needs.length === 1 ? "needs" : "need"} you
    </button>
  {/if}
  <button class="press h-7 min-w-0 shrink-0 gap-1.5 px-2 whitespace-nowrap" title={first ? "Work runs on This PC" : `Work runs on This PC and ${worst ? "trading-node-frankfurt-02.contabo-vps.internal" : "vps-fra"}`} onclick={() => shell.go("settings")}>
    <Icon name="laptop" class="size-3.5 shrink-0" />
    {first ? "This PC" : "This PC + 1 server"}
  </button>

  <span class="flex-1"></span>

  <div class="flex shrink-0 items-center gap-1" role="group" aria-label="Market clocks">
    {#each cities as c (c.id)}<MarketClock city={c} />{/each}
  </div>

  <span class="flex-1"></span>

  <span class="sb-demo shrink-0 px-2 whitespace-nowrap">{first ? "Nothing connected" : "Demo data"}</span>
  {#if !first}
    <button class="press h-7 shrink-0 gap-1.5 px-2 whitespace-nowrap" title="Open Trading" onclick={() => shell.go("trading")}>
      <span class="dot size-1.5 {level === 'trading' ? 'text-live' : level === 'paused' ? 'text-paper' : 'text-down'}"></span>
      <span class="text-foreground">{label[level]}</span>
    </button>
    <Menu.Root onOpenChange={(o) => !o && (armed = false)}>
      <Menu.Trigger>
        {#snippet child({ props })}
          <button {...props} class="text-down hover:bg-down/15 flex h-7 shrink-0 items-center gap-1.5 rounded-md px-2 font-medium whitespace-nowrap transition-colors duration-150 active:scale-[0.97]">
            <Icon name="stop" class="size-3.5" />Stop<Icon name="chevron-down" class="size-3" />
          </button>
        {/snippet}
      </Menu.Trigger>
      <Menu.Content side="top" align="end" class="w-80">
        <Menu.Label>Stop trading, mildest first</Menu.Label>
        {#if level !== "trading"}
          <Menu.Item onclick={() => set("trading")}><Icon name="check" />Resume trading on both nodes</Menu.Item>
          <Menu.Separator />
        {/if}
        <Menu.Item onclick={() => set("paused")}>
          <span class="flex flex-col"><span>Pause new trades</span><span class="text-muted-foreground text-sm">Open positions stay and keep their stops</span></span>
        </Menu.Item>
        <Menu.Item onclick={() => set("stopped")}>
          <span class="flex flex-col"><span>Stop one node…</span><span class="text-muted-foreground text-sm">Home node, or Frankfurt node</span></span>
        </Menu.Item>
        <Menu.Separator />
        <Menu.Item variant="destructive" closeOnSelect={false} onclick={() => (armed ? set("closed") : (armed = true))}>
          <span class="flex flex-col">
            <span>{armed ? "Click again to close everything" : "Close all positions and stop"}</span>
            <span class="text-sm opacity-80">Both nodes, 2 open positions. This cannot be undone.</span>
          </span>
        </Menu.Item>
      </Menu.Content>
    </Menu.Root>
  {/if}
</footer>

<style>
  /* The bar never overflows: on a narrow window or big text the data-source
     note goes first, then the market names shorten to codes. */
  .sb {
    container-type: inline-size;
  }
  @container (max-width: 66rem) {
    .sb-demo {
      display: none;
    }
  }
  @container (max-width: 58rem) {
    .sb :global(.clk-full) {
      display: none;
    }
    .sb :global(.clk-short) {
      display: inline;
    }
  }
</style>
