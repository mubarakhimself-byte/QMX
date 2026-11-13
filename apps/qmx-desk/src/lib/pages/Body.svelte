<script lang="ts">
  import Rows from "$lib/qmx/Rows.svelte";
  import DataTable from "$lib/qmx/DataTable.svelte";
  import Stats from "$lib/qmx/Stats.svelte";
  import Spark from "$lib/qmx/Spark.svelte";
  import { things } from "$lib/shell/things.svelte";
  import { shell } from "$lib/shell/state.svelte";
  import { kindName, type Body } from "$lib/shell/model";
  import Thing from "./Thing.svelte";

  // One renderer for every section body, built-in or from a mini app.
  let { body, big = false }: { body: Body; big?: boolean } = $props();
</script>

{#if body.t === "stats"}
  <Stats stats={body.stats} {big} />
{:else if body.t === "spark"}
  <div class="h-full min-h-[9rem]" style:--line={body.mode ? `var(--${body.mode})` : undefined}>
    <Spark series={body.series} note={body.note} />
  </div>
{:else if body.t === "rows"}
  <Rows rows={body.rows} />
{:else if body.t === "table"}
  <DataTable cols={body.cols} rows={body.rows} />
{:else if body.t === "facts"}
  <dl class="grid grid-cols-[minmax(0,auto)_minmax(0,1fr)] gap-x-5 gap-y-2 p-2.5">
    {#each body.facts as [k, v] (k)}
      <dt class="text-muted-foreground truncate">{k}</dt>
      <dd class="min-w-0 [overflow-wrap:anywhere]">{v}</dd>
    {/each}
  </dl>
{:else if body.t === "links"}
  <ul class="flex flex-col">
    {#each body.ids as id (id)}
      {@const o = things.get(id)}
      {#if o}
        <li><Thing {o} hint={kindName[o.kind]} /></li>
      {/if}
    {/each}
  </ul>
{/if}
