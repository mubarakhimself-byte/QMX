<script lang="ts">
  /** Upcoming events that touch what the portfolio holds, and which Books they affect. */
  import Newspaper from "@lucide/svelte/icons/newspaper";
  import { cn } from "$lib/utils";
  import { EVENTS } from "../demo";
</script>

<ul class="h-full overflow-auto py-1">
  {#each EVENTS as e (e.title)}
    <li class="flex gap-3 border-b border-border/50 px-3 py-2">
      <Newspaper
        class={cn(
          "mt-0.5 size-4 shrink-0",
          e.impact === "high" ? "text-destructive" : "text-warning",
        )}
      />
      <div class="min-w-0">
        <p class="text-sm">
          <span class="font-medium">{e.title}</span>
          <span class="text-muted-foreground text-xs">{e.when}</span>
        </p>
        <p class="text-muted-foreground text-xs">
          Affects {e.affects.join(", ")}{e.impact === "high"
            ? " · protection window blocks new entries"
            : ""}
        </p>
      </div>
    </li>
  {/each}
</ul>
