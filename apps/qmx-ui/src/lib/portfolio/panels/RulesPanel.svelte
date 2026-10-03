<script lang="ts">
  /** The selected Book's limits as a stack: each OK, near or tripped, with how close it is. */
  import Plus from "@lucide/svelte/icons/plus";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { bookById } from "../demo";
  import { RULE_TONE } from "../bits";
  import { portfolio } from "../portfolio.svelte";

  const b = $derived(bookById(portfolio.book)!);
</script>

<div class="flex h-full flex-col">
  <ul class="min-h-0 flex-1 overflow-auto">
    {#each b.rules as r (r.name)}
      <li class="border-b border-border/50 px-3 py-2">
        <div class="flex items-center gap-2 text-sm">
          <span class={cn("size-2 rounded-full", RULE_TONE[r.state])}></span>
          <span class="font-medium">{r.name}</span>
          <span class="text-muted-foreground ml-auto text-xs">{r.state}</span>
        </div>
        <div class="mt-1.5 flex items-center gap-2">
          <span class="bg-muted h-1.5 flex-1 overflow-hidden rounded-full">
            <span
              class={cn("block h-full", RULE_TONE[r.state])}
              style="width:{Math.min(1, r.used) * 100}%"
            ></span>
          </span>
          <span class="num text-xs">{r.value}</span>
          <span class="text-muted-foreground text-xs">of {r.limit}</span>
        </div>
      </li>
    {/each}
  </ul>
  <button
    type="button"
    class="text-muted-foreground hover:text-foreground flex h-9 shrink-0 items-center gap-1.5 border-t px-3 text-xs"
    onclick={() =>
      workbench.notify(
        `Adding a rule drafts a new version of ${b.name}. Describe it to the Portfolio copilot, or pick one from the Lab.`,
      )}><Plus class="size-3.5" />Add a rule</button
  >
</div>
