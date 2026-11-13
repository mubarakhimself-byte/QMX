<script lang="ts">
  import Thing from "$lib/pages/Thing.svelte";
  import { things } from "$lib/shell/things.svelte";
  import { decided } from "$lib/shell/desk";
  import type { Obj } from "$lib/shell/model";
  import { tone } from "../state";
  import { panelSize } from "../tiles/panel-size";
  import Fit from "../Fit.svelte";
  import Mini from "../Mini.svelte";

  // What waits for him. Compact: the count and the names. Regular: each
  // with where it comes from. Expanded: proposals show their evidence in
  // the row. Under the list, what he decided lately fills the rest.
  const size = panelSize();
  const ask = (o: Obj) => (o.kind === "proposal" ? "Decide" : o.kind === "session" ? "Approve" : "Fix");
  const list = $derived(things.needs);
</script>

<div class="flex h-full min-h-0 flex-col">
  {#if size.mode === "compact"}
    <p class="flex shrink-0 items-baseline gap-2 px-2.5 pt-1"><span class="display num text-needs text-3xl font-semibold">{list.length}</span><span class="text-muted-foreground">wait for you</span></p>
  {/if}
  {#if list.length}
    <ul class="min-h-0 flex-[0_1_auto] overflow-x-hidden overflow-y-auto">
      {#each list as o (o.id)}
        <li>
          <Thing {o} list="needs" hint={ask(o)} slim={size.mode === "compact"} />
          {#if size.mode === "expanded" && o.evidence}
            {@const ev = o.evidence}
            <div class="text-muted-foreground mb-1 ml-8 flex min-w-0 flex-wrap items-center gap-x-5 gap-y-1 text-sm">
              <span class={tone[ev.verdictTone]}>{ev.verdict}</span>
              <Mini series={ev.series} color="var(--paper)" class="h-5 w-28" />
              {#each ev.stats.slice(0, 3) as s (s.label)}<span class="whitespace-nowrap">{s.label} <span class="num text-foreground {s.tone ? tone[s.tone] : ''}">{s.value}</span></span>{/each}
            </div>
          {/if}
        </li>
      {/each}
    </ul>
  {:else}
    <p class="text-muted-foreground flex shrink-0 items-center gap-2 p-2.5"><span class="dot text-up"></span>Nothing waits for you.</p>
  {/if}
  <Fit items={decided} title="You decided lately" key={(d) => d.id}>
    {#snippet row(d)}
      <div class="flex min-w-0 items-start gap-3 px-2.5 py-1.5 text-sm">
        <span class="dot mt-[0.45em] {tone[d.tone]}"></span>
        <span class="text-muted-foreground min-w-0 flex-1 truncate" title={d.text}>{d.text}</span>
        <span class="num text-muted-foreground shrink-0">{d.when}</span>
      </div>
    {/snippet}
  </Fit>
</div>
