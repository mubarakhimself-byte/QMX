<script lang="ts">
  /**
   * Resources: what a Lab layout draws on, in one tile every strategy layout
   * shares (operator, 2026-10-02). One grouped list, no tabs (DESIGN-RULES.md
   * §4): the toolbox's items (workflows, bots, models, datasets, tests,
   * presets, reports), then machines. Data sources and model slots have
   * their own panels (+ Panel).
   */
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Settings2 from "@lucide/svelte/icons/settings-2";
  import { resolve } from "$app/paths";
  import { cn } from "$lib/utils";
  import EnvChip from "../EnvChip.svelte";
  import { ENVIRONMENTS, RUNS } from "../demo";
  import AssetsPanel from "./AssetsPanel.svelte";

  let open = $state(true);
</script>

{#snippet machines()}
  <section aria-label="Machines">
    <div class="flex h-8 items-center gap-1 pr-1 pl-2">
      <button
        type="button"
        class="flex min-w-0 flex-1 items-center gap-1 text-left text-xs"
        aria-expanded={open}
        onclick={() => (open = !open)}
      >
        <ChevronRight
          class={cn(
            "text-muted-foreground size-3.5 transition-transform",
            open && "rotate-90",
          )}
        />
        <span class="font-medium">Machines</span>
        <span class="text-muted-foreground tabular-nums"
          >{ENVIRONMENTS.length}</span
        >
      </button>
      <!-- eslint-disable svelte/no-navigation-without-resolve -- resolved path plus a query string -->
      <a
        href={`${resolve("/settings")}?tab=servers`}
        class="hover:bg-muted text-muted-foreground flex size-6 items-center justify-center rounded-md"
        aria-label="Add or manage machines in Settings"
        title="Add or manage machines in Settings"
        ><Settings2 class="size-3.5" /></a
      >
      <!-- eslint-enable svelte/no-navigation-without-resolve -->
    </div>
    {#if open}
      <ul>
        {#each ENVIRONMENTS as e (e.id)}
          {@const jobs = RUNS.filter(
            (r) =>
              r.env === e.id &&
              (r.status === "running" || r.status === "queued"),
          ).length}
          <li
            class="py-row flex items-center gap-2 pr-1 pl-7"
            title={`${e.where}${e.cost ? ` · ${e.cost}` : ""} · ${e.status}`}
          >
            <span class="min-w-0 flex-1 truncate">
              <EnvChip env={e.id} status={jobs ? "running" : "done"} />
            </span>
            <span class="num text-muted-foreground shrink-0 text-xs"
              >{e.slots[0]}/{e.slots[1]}</span
            >
          </li>
        {/each}
      </ul>
    {/if}
  </section>
{/snippet}

<AssetsPanel after={machines} />
