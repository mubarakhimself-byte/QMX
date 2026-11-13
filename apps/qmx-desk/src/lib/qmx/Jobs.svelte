<script lang="ts">
  import type { Row } from "$lib/shell/data";
  import Rows from "./Rows.svelte";

  // Many background jobs at a glance: one square per job, fill shows its state.
  let {
    jobs,
    rows = [],
  }: { jobs: { total: number; running: number; waiting: number; done: number }; rows?: Row[] } = $props();

  const nf = new Intl.NumberFormat("en");
  const shown = $derived(Math.min(jobs.total, 96));
  const cells = $derived.by(() => {
    const scale = shown / jobs.total;
    const run = Math.max(jobs.running ? 1 : 0, Math.round(jobs.running * scale));
    const wait = Math.max(jobs.waiting ? 1 : 0, Math.round(jobs.waiting * scale));
    return Array.from({ length: shown }, (_, i) => (i < wait ? "needs" : i < wait + run ? "run" : "done"));
  });
</script>

<div class="flex flex-col gap-3 p-2.5">
  <div class="flex flex-wrap gap-1" aria-hidden="true">
    {#each cells as c, i (i)}
      <span
        class="size-2.5 rounded-[2px] {c === 'needs' ? 'bg-needs' : c === 'run' ? 'bg-run' : 'bg-foreground/15'}"
      ></span>
    {/each}
  </div>
  <p class="text-muted-foreground text-sm">
    <span class="text-foreground num">{nf.format(jobs.running)}</span> running ·
    <span class="text-needs num">{nf.format(jobs.waiting)}</span> waiting on you ·
    <span class="num">{nf.format(jobs.done)}</span> done today
  </p>
</div>
<Rows {rows} />
