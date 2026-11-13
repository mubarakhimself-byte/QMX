<script lang="ts">
  import Thing from "$lib/pages/Thing.svelte";
  import Fit from "../Fit.svelte";
  import { things } from "$lib/shell/things.svelte";
  import { nodeLog } from "$lib/shell/desk";
  import { tone } from "../state";
  import { panelSize } from "../tiles/panel-size";

  // The trading nodes and their health. Compact: a line each. Regular: each
  // with where it runs and its account. Expanded: the same rows, then every
  // node's health checks and the units on it fill the rest.
  const size = panelSize();
  const nodes = $derived(things.all.filter((o) => o.kind === "node"));
  const checks = $derived(
    nodes.flatMap((n) => {
      const h = n.sections?.find((s) => s.id === "health")?.body;
      const u = n.sections?.find((s) => s.id === "units")?.body;
      return [
        { id: `${n.id}-h`, head: n.name },
        ...(h && h.t === "facts" ? h.facts.map(([k, v]) => ({ id: `${n.id}-${k}`, k, v, warn: /expires/i.test(v) })) : []),
        ...(u && u.t === "links" ? u.ids.map((id) => things.get(id)).filter((o) => !!o).map((o) => ({ id: `${n.id}-${o.id}`, unit: o })) : []),
      ];
    }),
  );
  // Then what the nodes did lately.
  const fill = $derived([...checks, { id: "log-h", head: "Lately" }, ...nodeLog.map((l) => ({ id: l.id, log: l }))]);
</script>

<div class="flex h-full min-h-0 flex-col">
  {#if !nodes.length}
    <p class="text-muted-foreground shrink-0 p-2.5" data-empty>No trading node yet. Start one on This PC to trade on a demo account.</p>
  {:else}
    <ul class="min-h-0 flex-[0_1_auto] overflow-x-hidden overflow-y-auto">
      {#each nodes as o (o.id)}<li><Thing {o} slim={size.mode === "compact"} /></li>{/each}
    </ul>
    <Fit items={fill} key={(x) => x.id}>
      {#snippet row(x)}
        {#if "head" in x}
          <h4 class="text-muted-foreground border-border/70 mx-2.5 mt-1.5 truncate border-t pt-2 pb-0.5 text-sm font-medium">{x.head}</h4>
        {:else if "log" in x}
          <div class="flex min-w-0 items-center gap-2.5 px-2.5 py-1 text-sm">
            <span class="dot size-1.5 {tone[x.log.tone]}"></span>
            <span class="text-muted-foreground shrink-0">{x.log.node}</span>
            <span class="min-w-0 flex-1 truncate" title={x.log.text}>{x.log.text}</span>
            <span class="num text-muted-foreground shrink-0">{x.log.when}</span>
          </div>
        {:else if "unit" in x}
          <div class="flex min-w-0 items-center gap-2.5 px-2.5 py-1 text-sm">
            <span class="dot size-1.5 {tone[x.unit.tone]}"></span>
            <span class="min-w-0 flex-1 truncate" title={x.unit.name}>{x.unit.name}</span>
            <span class="shrink-0 text-xs font-semibold uppercase {tone[x.unit.tone]}">{x.unit.word}</span>
          </div>
        {:else}
          <div class="flex min-w-0 items-center gap-2.5 px-2.5 py-1 text-sm">
            <span class="text-muted-foreground min-w-0 flex-1 truncate">{x.k}</span>
            <span class="shrink-0 {x.warn ? 'text-paper' : ''}">{x.v}</span>
          </div>
        {/if}
      {/snippet}
    </Fit>
  {/if}
</div>
