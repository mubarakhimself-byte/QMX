<script lang="ts">
  import Icon from "../Icon.svelte";
  import Thing from "$lib/pages/Thing.svelte";
  import { shell } from "$lib/shell/state.svelte";
  import { things } from "$lib/shell/things.svelte";
  import { jobs as allJobs, type Job, type JobState } from "$lib/shell/desk";
  import { panelSize } from "../tiles/panel-size";
  import Fit from "../Fit.svelte";

  // Today's jobs, one square each, grouped by the machine they run on.
  // Hover a square for the job's name; click it to open its run. A legend
  // names the colours. Compact: the squares and the counts. Regular: the
  // machines one under the other, then the runs that need watching.
  // Expanded: one column per machine, each with its own runs.
  const size = panelSize();
  const nf = new Intl.NumberFormat("en");
  const jobs = $derived(allJobs(things.fixture));
  const machines = $derived.by(() => {
    const m = new Map<string, Job[]>();
    for (const j of jobs) m.set(j.where, [...(m.get(j.where) ?? []), j]);
    return [...m.entries()].map(([where, list]) => ({ where, list }));
  });
  const count = (list: Job[], s: JobState) => list.filter((j) => j.state === s).length;
  const fill: Record<JobState, string> = { run: "bg-run", needs: "bg-needs", done: "bg-foreground/25", down: "bg-down", next: "outline outline-1 -outline-offset-1 outline-foreground/30" };
  const word: Record<JobState, string> = { run: "running", needs: "waits on you", done: "done", down: "failed", next: "next" };
  const legend: JobState[] = ["run", "needs", "done", "down", "next"];
  // Squares shown per machine; the rest are counted, never scrolled.
  const cap = $derived(size.mode === "compact" ? 48 : size.mode === "regular" ? 96 : 160);
  // Runs worth watching: running, waiting on him, failed.
  const active = $derived(things.all.filter((o) => o.kind === "run" && (o.word === "running" || o.tone === "needs" || o.word === "failed" || o.word === "queued")));
  const order = (o: { tone: string; word: string }) => (o.tone === "needs" ? 0 : o.word === "failed" ? 1 : o.word === "running" ? 2 : 3);
  const watch = $derived([...active].sort((a, b) => order(a) - order(b)));
  // Expanded: every run of the day per machine, the ones to watch first.
  const runs = $derived([...watch, ...things.all.filter((o) => o.kind === "run" && !active.includes(o))]);
  const open = (j: Job) => j.of && things.get(j.of) && shell.open({ id: j.of, list: "runs" });
</script>

{#snippet squares(list: Job[])}
  {@const shown = [...list].sort((a, b) => legend.indexOf(a.state) - legend.indexOf(b.state)).slice(0, cap)}
  <div class="flex flex-wrap gap-1">
    {#each shown as j (j.id)}
      <button class="sq {size.mode === 'expanded' ? 'size-4' : size.mode === 'regular' ? 'size-3' : 'size-2.5'} rounded-[2px] {fill[j.state]}" title="{j.name} · {word[j.state]}" aria-label="{j.name}, {word[j.state]}" onclick={() => open(j)}></button>
    {/each}
    {#if list.length > shown.length}<span class="num text-muted-foreground text-xs leading-3">+{nf.format(list.length - shown.length)}</span>{/if}
  </div>
{/snippet}

{#snippet machine(m: { where: string; list: Job[] })}
  <div class="flex min-w-0 flex-col gap-1.5">
    <p class="flex min-w-0 items-center gap-1.5 text-sm">
      <Icon name={m.where === "This PC" ? "laptop" : "server"} class="text-muted-foreground size-3.5 shrink-0" />
      <span class="min-w-0 truncate font-medium" title={m.where}>{m.where}</span>
      <span class="num text-muted-foreground ml-auto shrink-0"><span class="text-run">{nf.format(count(m.list, "run"))}</span> running · {nf.format(m.list.length)}</span>
    </p>
    {@render squares(m.list)}
  </div>
{/snippet}

<div class="flex h-full min-h-0 flex-col">
  {#if !jobs.length}
    <p class="text-muted-foreground shrink-0 p-2.5" data-empty>Nothing has run today. Backtests and workflows show here, by machine.</p>
  {:else}
    <div class="flex shrink-0 flex-col gap-2 px-2.5 pt-1 pb-2">
      <p class="text-muted-foreground flex flex-wrap gap-x-3 gap-y-0.5 text-xs" aria-label="Legend">
        {#each legend as s (s)}<span class="flex items-center gap-1"><span class="size-2.5 rounded-[2px] {fill[s]}"></span>{word[s]}</span>{/each}
      </p>
      {#if size.mode === "expanded"}
        <div class="grid gap-4" style:grid-template-columns="repeat({machines.length}, minmax(0, 1fr))">
          {#each machines as m (m.where)}{@render machine(m)}{/each}
        </div>
      {:else}
        {#each machines as m (m.where)}{@render machine(m)}{/each}
      {/if}
    </div>
    {#if size.mode === "expanded"}
      <div class="grid min-h-0 flex-1 gap-4" style:grid-template-columns="repeat({machines.length}, minmax(0, 1fr))">
        {#each machines as m (m.where)}
          <Fit items={[...runs.filter((o) => o.where === m.where).map((o) => ({ id: o.id, o })), ...m.list.filter((j) => j.state !== "done").concat(m.list.filter((j) => j.state === "done")).map((j) => ({ id: j.id, j }))]} title="Runs on {m.where}" key={(x) => x.id}>
            {#snippet row(x)}
              {#if "o" in x && x.o}<Thing o={x.o} list="runs" />
              {:else if "head" in x}<h4 class="text-muted-foreground border-border/70 mx-2.5 mt-1.5 border-t pt-2 pb-0.5 text-sm font-medium">{x.head}</h4>
              {:else if "j" in x && x.j}
                <button class="pick flex w-full min-w-0 items-center gap-2.5 rounded-md px-2.5 py-1 text-left text-sm" onclick={() => x.j && open(x.j)}>
                  <span class="size-2.5 shrink-0 rounded-[2px] {fill[x.j.state]}"></span>
                  <span class="min-w-0 flex-1 truncate" title={x.j.name}>{x.j.name}</span>
                  <span class="text-muted-foreground shrink-0">{word[x.j.state]}</span>
                </button>
              {/if}
            {/snippet}
          </Fit>
        {/each}
      </div>
    {:else}
      <Fit items={watch} title={size.mode === "compact" ? undefined : "Runs to watch"} key={(o) => o.id} onmore={() => shell.go("runs")}>
        {#snippet row(o)}<Thing {o} list="runs" slim />{/snippet}
      </Fit>
    {/if}
  {/if}
</div>

<style>
  .sq {
    transition: transform 120ms ease-out;
  }
  .sq:hover {
    transform: scale(1.35);
  }
</style>
