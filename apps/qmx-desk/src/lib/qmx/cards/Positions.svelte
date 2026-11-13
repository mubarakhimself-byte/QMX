<script lang="ts">
  import Icon from "../Icon.svelte";
  import Fit from "../Fit.svelte";
  import { shell } from "$lib/shell/state.svelte";
  import { things } from "$lib/shell/things.svelte";
  import { positions, type Position } from "$lib/shell/desk";
  import { panelSize } from "../tiles/panel-size";

  // Open positions, then what closed today. Every row keeps the unit's name
  // and its live or paper mark; narrow widgets drop the other columns first.
  // Compact: name, market and result. Regular: side and entry too. Expanded:
  // stop, when it opened and where it runs.
  const size = panelSize();
  const p = $derived(positions(things.fixture));
  const sign = (s: string) => (s.startsWith("+") ? "text-up" : s.startsWith("-") ? "text-down" : "");
  const cols = $derived(
    size.mode === "compact"
      ? (["sym", "now"] as const)
      : size.mode === "regular"
        ? (["sym", "side", "entry", "now"] as const)
        : (["sym", "side", "entry", "stop", "opened", "where", "now"] as const),
  );
  const head: Record<string, string> = { sym: "Market", side: "Side", entry: "Entry", stop: "Stop", opened: "Opened", where: "Runs on", now: "Now" };
  const mark = (m: "live" | "paper") => (m === "live" ? "text-live" : "text-paper");
</script>

<div class="flex h-full min-h-0 flex-col">
  {#if !p.open.length}
    <p class="text-muted-foreground shrink-0 p-2.5" data-empty>No open positions. Trades your units open show here.</p>
  {:else}
    <div class="pos min-h-0 flex-[0_1_auto] overflow-x-hidden overflow-y-auto">
      <table class="w-full border-separate border-spacing-0">
        <thead>
          <tr>
            <th class="text-muted-foreground bg-panel border-border sticky top-0 border-b px-2.5 py-1.5 text-left text-sm font-medium">Unit</th>
            {#each cols as c (c)}<th class="c-{c} text-muted-foreground bg-panel border-border sticky top-0 border-b px-2.5 py-1.5 text-right text-sm font-medium whitespace-nowrap">{head[c]}</th>{/each}
          </tr>
        </thead>
        <tbody>
          {#each p.open as r (r.id)}
            <tr class="hover:bg-accent/50 cursor-pointer transition-colors duration-150" onclick={() => shell.open({ id: r.unit, list: "units" })}>
              <td class="border-border/60 max-w-0 border-b px-2.5 py-2 text-left">
                <span class="flex min-w-0 items-center gap-2">
                  <span class="shrink-0 text-xs font-semibold uppercase {mark(r.mode)}">{r.mode}</span>
                  <span class="min-w-0 truncate font-medium" title={r.name}>{r.name}</span>
                </span>
              </td>
              {#each cols as c (c)}
                <td class="c-{c} border-border/60 border-b px-2.5 py-2 text-right whitespace-nowrap {c === 'now' ? sign(r.now) : ''} {c !== 'where' && c !== 'side' ? 'num' : ''}">
                  {#if c === "where"}
                    <span class="text-muted-foreground inline-flex max-w-[12rem] items-center gap-1.5"><Icon name={r.where === "This PC" ? "laptop" : "server"} class="size-3.5 shrink-0" /><span class="truncate" title={r.where}>{r.where}</span></span>
                  {:else}{r[c as keyof Position]}{/if}
                </td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
  <Fit items={p.closed} title="Closed lately" key={(c) => c.id}>
    {#snippet row(c)}
      <button class="pick flex w-full min-w-0 items-center gap-3 rounded-md px-2.5 py-1.5 text-left text-sm" onclick={() => shell.open({ id: c.unit, list: "units" })}>
        <span class="shrink-0 text-xs font-semibold uppercase {mark(c.mode)}">{c.mode}</span>
        <span class="min-w-0 flex-1 truncate" title={c.name}>{c.name}</span>
        <span class="num text-muted-foreground shrink-0">{c.sym}</span>
        {#if size.mode !== "compact"}<span class="text-muted-foreground shrink-0">{c.side}</span>{/if}
        <span class="num shrink-0 {sign(c.result)}">{c.result}</span>
        <span class="num text-muted-foreground w-[4.5rem] shrink-0 text-right">{c.at}</span>
      </button>
    {/snippet}
  </Fit>
</div>

<style>
  .pos {
    container-type: inline-size;
  }
  /* Narrow: least important columns go first; name, mode and result stay. */
  @container (max-width: 34rem) {
    .c-opened,
    .c-where,
    .c-stop {
      display: none;
    }
  }
  @container (max-width: 26rem) {
    .c-entry,
    .c-side {
      display: none;
    }
  }
</style>
