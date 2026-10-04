<script lang="ts">
  /** What needs you right now, from every screen, newest problems first. */
  import ArrowUpRight from "@lucide/svelte/icons/arrow-up-right";
  import CircleCheck from "@lucide/svelte/icons/circle-check";
  import { resolve } from "$app/paths";
  import { cn } from "$lib/utils";
  import { needs } from "../needs";

  const list = $derived(needs());
  const TONE = {
    warning: "bg-warning",
    info: "bg-info",
    destructive: "bg-destructive",
  };
</script>

<div class="h-full overflow-auto p-2">
  {#if list.length}
    <ul class="flex flex-col gap-1.5">
      <!-- eslint-disable svelte/no-navigation-without-resolve -->
      {#each list as n (n.id)}
        <li>
          <a
            href={`${resolve(n.path as "/")}${n.query ? `?${n.query}` : ""}`}
            class="hover:bg-muted/60 flex items-start gap-3 rounded-lg border px-3 py-2.5"
          >
            <span
              class={cn("mt-1.5 size-2 shrink-0 rounded-full", TONE[n.tone])}
            ></span>
            <span class="min-w-0 flex-1">
              <span class="block text-sm font-medium">{n.title}</span>
              <span class="text-muted-foreground block text-sm"
                >{n.kind} · {n.why}</span
              >
            </span>
            <ArrowUpRight class="text-muted-foreground mt-1 size-4 shrink-0" />
          </a>
        </li>
      {/each}
      <!-- eslint-enable svelte/no-navigation-without-resolve -->
    </ul>
  {:else}
    <p class="text-muted-foreground flex items-center gap-2 p-3 text-sm">
      <CircleCheck class="text-success size-4" />Nothing needs you.
    </p>
  {/if}
</div>
