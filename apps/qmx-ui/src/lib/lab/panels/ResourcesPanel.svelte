<script lang="ts">
  /**
   * Resources: everything a Lab layout draws on, in one tile that every
   * layout shares (operator, 2026-10-02): items (workflows, bots, models,
   * tests, presets, reports), data, machines and model slots. It works as a
   * quick menu into the Library; adding a machine goes to Settings.
   */
  import Boxes from "@lucide/svelte/icons/boxes";
  import Database from "@lucide/svelte/icons/database";
  import Cpu from "@lucide/svelte/icons/cpu";
  import Plug from "@lucide/svelte/icons/plug";
  import LibraryBig from "@lucide/svelte/icons/library-big";
  import Settings2 from "@lucide/svelte/icons/settings-2";
  import { resolve } from "$app/paths";
  import { cn } from "$lib/utils";
  import EnvChip from "../EnvChip.svelte";
  import { ENVIRONMENTS, RUNS } from "../demo";
  import AssetsPanel from "./AssetsPanel.svelte";
  import DataPanel from "./DataPanel.svelte";
  import SlotsPanel from "./SlotsPanel.svelte";

  const TABS = [
    { id: "items", label: "Items", icon: Boxes },
    { id: "data", label: "Data", icon: Database },
    { id: "machines", label: "Machines", icon: Cpu },
    { id: "slots", label: "Slots", icon: Plug },
  ] as const;
  let tab = $state<(typeof TABS)[number]["id"]>("items");
</script>

<div class="flex h-full flex-col">
  <div
    class="flex h-9 shrink-0 items-center gap-0.5 border-b px-1.5"
    role="tablist"
    aria-label="Resources"
  >
    {#each TABS as t (t.id)}
      <button
        type="button"
        role="tab"
        aria-selected={tab === t.id}
        class={cn(
          "flex h-7 items-center gap-1.5 rounded-md px-2 text-xs",
          tab === t.id
            ? "bg-muted text-foreground"
            : "text-muted-foreground hover:text-foreground",
        )}
        title={t.label}
        onclick={() => (tab = t.id)}
        ><t.icon class="size-3.5" /><span class="hidden @[16rem]:inline"
          >{t.label}</span
        ></button
      >
    {/each}
    <a
      href={resolve("/library")}
      class="text-muted-foreground hover:text-foreground hover:bg-muted ml-auto flex size-7 items-center justify-center rounded-md"
      aria-label="Open the Library"
      title="Open the Library"><LibraryBig class="size-3.5" /></a
    >
  </div>
  <div class="min-h-0 flex-1">
    {#if tab === "items"}
      <AssetsPanel />
    {:else if tab === "data"}
      <DataPanel />
    {:else if tab === "slots"}
      <SlotsPanel />
    {:else}
      <div class="flex h-full flex-col">
        <ul class="min-h-0 flex-1 overflow-auto">
          {#each ENVIRONMENTS as e (e.id)}
            {@const jobs = RUNS.filter(
              (r) =>
                r.env === e.id &&
                (r.status === "running" || r.status === "queued"),
            ).length}
            <li class="border-b border-border/50 px-3 py-2">
              <div class="flex items-center gap-2">
                <EnvChip env={e.id} status={jobs ? "running" : "done"} />
                <span class="text-muted-foreground ml-auto text-xs"
                  >{e.status}</span
                >
              </div>
              <div class="mt-1.5 flex items-center gap-2">
                <span class="bg-muted h-1 flex-1 overflow-hidden rounded-full">
                  <span
                    class={cn(
                      "block h-full",
                      e.kind === "local" ? "bg-primary" : "bg-info",
                    )}
                    style="width: {(e.slots[0] / e.slots[1]) * 100}%"
                  ></span>
                </span>
                <span class="num text-muted-foreground text-xs"
                  >{e.slots[0]}/{e.slots[1]}</span
                >
              </div>
              <p class="text-muted-foreground mt-1 text-xs">
                {e.where}{e.cost ? ` · ${e.cost}` : ""} · {jobs} job{jobs === 1
                  ? ""
                  : "s"}
              </p>
            </li>
          {/each}
        </ul>
        <!-- eslint-disable svelte/no-navigation-without-resolve -- resolved path plus a query string -->
        <a
          href={`${resolve("/settings")}?tab=compute`}
          class="text-muted-foreground hover:text-foreground flex h-9 shrink-0 items-center gap-1.5 border-t px-3 text-xs"
          ><Settings2 class="size-3.5" />Add or manage machines in Settings</a
        >
        <!-- eslint-enable svelte/no-navigation-without-resolve -->
      </div>
    {/if}
  </div>
</div>
