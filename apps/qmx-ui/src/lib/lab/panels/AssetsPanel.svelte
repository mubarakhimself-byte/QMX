<script lang="ts">
  /**
   * The Lab's toolbox: workflows, bots, models, datasets, features, saved
   * tests, presets and reports. Every group has an "add your own" path.
   * Groups the docs don't define yet are marked new scope.
   */
  import Search from "@lucide/svelte/icons/search";
  import Plus from "@lucide/svelte/icons/plus";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import MessageSquarePlus from "@lucide/svelte/icons/message-square-plus";
  import { Input } from "$lib/components/ui/input";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import EnvChip from "../EnvChip.svelte";
  import { ASSETS, ASSET_GROUPS } from "../demo";

  let q = $state("");
  let closed = $state<string[]>(["report", "preset"]);
  const toggle = (k: string) =>
    (closed = closed.includes(k)
      ? closed.filter((c) => c !== k)
      : [...closed, k]);
  const match = (name: string) =>
    !q || name.toLowerCase().includes(q.toLowerCase());
</script>

<div class="flex h-full flex-col">
  <div class="relative shrink-0 border-b p-2">
    <Search
      class="text-muted-foreground pointer-events-none absolute top-1/2 left-4 size-3.5 -translate-y-1/2"
    />
    <Input
      bind:value={q}
      placeholder="Find anything"
      aria-label="Find in the toolbox"
      class="h-8 pl-8"
    />
  </div>
  <div class="min-h-0 flex-1 overflow-auto py-1">
    {#each ASSET_GROUPS as g (g.kind)}
      {@const items = ASSETS.filter((a) => a.kind === g.kind && match(a.name))}
      {#if !q || items.length}
        <section>
          <div class="group/h flex h-8 items-center gap-1 pr-1 pl-2">
            <button
              type="button"
              class="flex min-w-0 flex-1 items-center gap-1 text-left text-xs"
              aria-expanded={!closed.includes(g.kind)}
              onclick={() => toggle(g.kind)}
            >
              <ChevronRight
                class={cn(
                  "text-muted-foreground size-3.5 transition-transform",
                  !closed.includes(g.kind) && "rotate-90",
                )}
              />
              <span class="font-medium">{g.label}</span>
              <span class="text-muted-foreground tabular-nums"
                >{items.length}</span
              >
              {#if g.scope === "new"}<span
                  class="text-muted-foreground ml-1 rounded border px-1 text-xs"
                  >new scope</span
                >{/if}
            </button>
            <button
              type="button"
              class="hover:bg-muted text-muted-foreground flex size-6 items-center justify-center rounded-md opacity-0 group-hover/h:opacity-100 focus-visible:opacity-100"
              aria-label={g.add}
              onclick={() =>
                workbench.notify(
                  `${g.add}: the Lab copilot can scaffold it, or build it in the editor.`,
                )}><Plus class="size-3.5" /></button
            >
          </div>
          {#if !closed.includes(g.kind)}
            <ul>
              {#each items as a (a.id)}
                <li
                  class="group/i hover:bg-muted/50 flex items-center gap-2 py-1.5 pr-1 pl-7"
                >
                  <span class="min-w-0 flex-1">
                    <span class="block truncate text-sm">{a.name}</span>
                    <span class="text-muted-foreground block truncate text-xs"
                      >{a.meta}</span
                    >
                  </span>
                  {#if a.env}<EnvChip env={a.env} compact />{/if}
                  <button
                    type="button"
                    class="hover:bg-muted text-muted-foreground flex size-6 shrink-0 items-center justify-center rounded-md opacity-0 group-hover/i:opacity-100 focus-visible:opacity-100"
                    aria-label={`Add ${a.name} to copilot`}
                    onclick={() => workbench.addRef(a.name)}
                    ><MessageSquarePlus class="size-3.5" /></button
                  >
                </li>
              {/each}
            </ul>
          {/if}
        </section>
      {/if}
    {/each}
  </div>
</div>
