<script lang="ts">
  /**
   * Shown instead of the tiles when the chosen machine has nothing for this
   * layout: says so plainly, points to where its work is, and offers to start
   * something there. Never a dead end.
   */
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import Layers from "@lucide/svelte/icons/layers";
  import Plus from "@lucide/svelte/icons/plus";
  import { Button } from "$lib/components/ui/button";
  import EnvChip from "./EnvChip.svelte";
  import { activity, envById } from "./demo";
  import { lab } from "./lab.svelte";

  let { machine, onstart }: { machine: string; onstart: () => void } = $props();

  const env = $derived(envById(machine));
  const VERB: Record<string, string> = {
    build: "being built",
    test: "being tested",
    train: "training",
    compare: "to compare",
  };
  const elsewhere = $derived(
    lab.layouts
      .filter((l) => l.id !== lab.activeId)
      .map((l) => ({ l, n: activity(machine, l.id) }))
      .filter((x) => x.n > 0),
  );
</script>

<div class="flex h-full items-center justify-center p-6">
  <div class="tile flex max-w-lg flex-col gap-4 rounded-xl p-6">
    <div class="flex items-center gap-2">
      <EnvChip env={machine} />
      <span class="text-muted-foreground text-xs">{env?.where}</span>
    </div>
    <div>
      <h2 class="text-lg font-semibold">
        Nothing {VERB[lab.activeId] ?? "here"} on {env?.name}
      </h2>
      <p class="text-muted-foreground mt-1 text-sm">
        {#if elsewhere.length}
          Its work is in other layouts. Jump there, start something here, or go
          back to every machine.
        {:else}
          This machine is idle. Start something on it, or go back to every
          machine.
        {/if}
      </p>
    </div>
    {#if elsewhere.length}
      <ul class="grid gap-1.5">
        {#each elsewhere as { l, n } (l.id)}
          <li>
            <button
              type="button"
              class="hover:bg-muted flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left text-sm"
              onclick={() => (lab.activeId = l.id)}
            >
              <span class="font-medium">{l.name}</span>
              <span class="text-muted-foreground text-xs"
                >{n} item{n === 1 ? "" : "s"} on this machine</span
              >
              <ArrowRight class="text-muted-foreground ml-auto size-4" />
            </button>
          </li>
        {/each}
      </ul>
    {/if}
    <div class="flex flex-wrap gap-2">
      <Button size="sm" onclick={onstart}
        ><Plus />Start something on {env?.name}</Button
      >
      <Button variant="ghost" size="sm" onclick={() => lab.connect(null)}
        ><Layers />Show all machines</Button
      >
    </div>
  </div>
</div>
