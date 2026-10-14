<script lang="ts">
  /**
   * What is running: copilot sessions working on their own, and jobs on your
   * servers. Jobs from one batch (e.g. nine training runs on one provider)
   * fold into one row you can open.
   */
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import { resolve } from "$app/paths";
  import { cn } from "$lib/utils";
  import { copilot } from "$lib/copilot/store.svelte";
  import { TASKS } from "$lib/copilot/demo";
  import { panelSize } from "$lib/workbench/tiles/panel-size";

  type Job = {
    id: string;
    name: string;
    where: string;
    state: "running" | "waiting" | "scheduled" | "done";
    progress: number;
    log: string[];
    batch?: string;
  };
  type Row =
    | { kind: "job"; job: Job }
    | { kind: "batch"; id: string; name: string; where: string; jobs: Job[] };

  // Sample: a hyper-parameter search the Lab sent to Colab as nine runs.
  const TRIALS: Job[] = Array.from({ length: 9 }, (_, i) => ({
    id: `t-trial-${i + 1}`,
    name: `Trial ${i + 1}: depth ${4 + (i % 3)}, rate 0.0${1 + Math.floor(i / 3)}`,
    where: "colab",
    state: i < 3 ? "done" : i < 7 ? "running" : "waiting",
    progress: i < 3 ? 100 : i < 7 ? 20 + i * 9 : 0,
    log: [i < 3 ? `validation loss 0.4${i + 1}` : "fitting"],
    batch: "Train Breakout scorer",
  }));
  const JOBS: Job[] = [...TASKS, ...TRIALS];

  const size = panelSize();
  const sessions = $derived(
    copilot.sessions.filter((s) => !s.parent && s.status !== "done"),
  );
  const rows = $derived.by((): Row[] => {
    const out: Row[] = [];
    const batches: Record<string, Job[]> = {};
    for (const j of JOBS) {
      if (!j.batch) {
        out.push({ kind: "job", job: j });
        continue;
      }
      const key = `${j.batch}@${j.where}`;
      if (!batches[key]) {
        batches[key] = [];
        out.push({
          kind: "batch",
          id: key,
          name: j.batch,
          where: j.where,
          jobs: batches[key],
        });
      }
      batches[key].push(j);
    }
    return out;
  });
  const running = $derived(
    sessions.filter((s) => s.status === "running").length +
      JOBS.filter((j) => j.state === "running").length,
  );
  let open = $state<Record<string, boolean>>({});
  const avg = (jobs: Job[]) =>
    jobs.reduce((t, j) => t + j.progress, 0) / jobs.length;
  const count = (jobs: Job[], state: Job["state"]) =>
    jobs.filter((j) => j.state === state).length;
</script>

{#snippet bar(progress: number)}
  <div class="bg-muted mt-1 h-1 overflow-hidden rounded-full">
    <span class="bg-info block h-full" style="width:{progress}%"></span>
  </div>
{/snippet}

{#snippet job(j: Job, nested = false)}
  <li class={cn("py-row", nested && "pl-6")}>
    <div class="flex items-center gap-2">
      <span class="min-w-0 flex-1 truncate text-sm">{j.name}</span>
      <span class="text-muted-foreground shrink-0 text-xs"
        >{nested
          ? j.state === "running"
            ? `${j.progress}%`
            : j.state
          : j.where}</span
      >
    </div>
    {#if j.state === "running"}{@render bar(j.progress)}{/if}
    {#if size.mode === "expanded" || (j.state !== "running" && !nested)}
      <p class="text-muted-foreground truncate text-xs">{j.log.at(-1)}</p>
    {/if}
  </li>
{/snippet}

{#if size.mode === "compact"}
  <div class="p-panel gap-row flex h-full flex-col overflow-hidden">
    <p class="num text-2xl font-semibold">{running}</p>
    <p class="text-muted-foreground text-xs">running now</p>
    <ul class="mt-group flex flex-col gap-0.5 text-sm">
      {#each sessions as s (s.id)}
        <li class="flex min-w-0 items-center gap-2">
          <span
            class={cn(
              "size-1.5 shrink-0 rounded-full",
              s.status === "running" ? "bg-info" : "bg-warning",
            )}
          ></span>
          <span class="truncate">{s.title}</span>
        </li>
      {/each}
      {#each rows as r (r.kind === "job" ? r.job.id : r.id)}
        <li class="flex min-w-0 items-center gap-2">
          <span class="bg-info size-1.5 shrink-0 rounded-full"></span>
          <span class="truncate"
            >{r.kind === "job"
              ? r.job.name
              : `${r.jobs.length} × ${r.name}`}</span
          >
        </li>
      {/each}
    </ul>
  </div>
{:else}
  <div class="p-panel gap-group flex h-full flex-col overflow-auto">
    <section aria-label="Copilot sessions">
      <h4 class="text-muted-foreground pb-row text-xs font-medium">Sessions</h4>
      <ul class="flex flex-col">
        <!-- eslint-disable svelte/no-navigation-without-resolve -->
        {#each sessions as s (s.id)}
          <li>
            <a
              href={`${resolve("/copilot")}?session=${s.id}`}
              class="hover:bg-muted/60 py-row -mx-2 flex items-center gap-2 rounded-md px-2"
            >
              <span
                class={cn(
                  "size-2 shrink-0 rounded-full",
                  s.status === "running"
                    ? "bg-info remote-pulse"
                    : "bg-warning",
                )}
              ></span>
              <span class="min-w-0 flex-1 truncate text-sm">{s.title}</span>
              <span class="text-muted-foreground shrink-0 text-xs"
                >{s.status === "running" ? "Running" : "Waiting"} · {s.age}</span
              >
            </a>
          </li>
        {/each}
        <!-- eslint-enable svelte/no-navigation-without-resolve -->
      </ul>
    </section>
    <section aria-label="Jobs on your servers">
      <h4 class="text-muted-foreground pb-row text-xs font-medium">Jobs</h4>
      <ul class="flex flex-col">
        {#each rows as r (r.kind === "job" ? r.job.id : r.id)}
          {#if r.kind === "job"}
            {@render job(r.job)}
          {:else}
            <li class="py-row">
              <button
                type="button"
                class="hover:bg-muted/60 -mx-2 flex w-[calc(100%+1rem)] items-center gap-2 rounded-md px-2 text-left"
                aria-expanded={!!open[r.id]}
                onclick={() => (open[r.id] = !open[r.id])}
              >
                <ChevronRight
                  class={cn(
                    "text-muted-foreground size-3.5 shrink-0 transition-transform",
                    open[r.id] && "rotate-90",
                  )}
                />
                <span class="min-w-0 flex-1 truncate text-sm"
                  >{r.name}
                  <span class="text-muted-foreground num"
                    >× {r.jobs.length}</span
                  ></span
                >
                <span class="text-muted-foreground shrink-0 text-xs"
                  >{count(r.jobs, "done")} done · {count(r.jobs, "running")} running
                  · {r.where}</span
                >
              </button>
              {@render bar(avg(r.jobs))}
              {#if open[r.id]}
                <ul class="pt-row flex flex-col">
                  {#each r.jobs as j (j.id)}{@render job(j, true)}{/each}
                </ul>
              {/if}
            </li>
          {/if}
        {/each}
      </ul>
    </section>
  </div>
{/if}
