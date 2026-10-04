<script lang="ts">
  /** What is running: copilot sessions working on their own, and background jobs on your servers. */
  import { resolve } from "$app/paths";
  import { cn } from "$lib/utils";
  import { copilot } from "$lib/copilot/store.svelte";
  import { TASKS } from "$lib/copilot/demo";

  const sessions = $derived(
    copilot.sessions.filter((s) => !s.parent && s.status !== "done"),
  );
</script>

<div class="h-full overflow-auto p-2">
  <p class="text-muted-foreground px-1 pb-1 text-[13px] font-semibold">
    Copilot sessions
  </p>
  <ul class="mb-3 flex flex-col gap-1">
    <!-- eslint-disable svelte/no-navigation-without-resolve -->
    {#each sessions as s (s.id)}
      <li>
        <a
          href={`${resolve("/copilot")}?session=${s.id}`}
          class="hover:bg-muted/60 flex items-center gap-2 rounded-md px-2 py-1.5"
        >
          <span
            class={cn(
              "size-2 shrink-0 rounded-full",
              s.status === "running" ? "bg-info remote-pulse" : "bg-warning",
            )}
          ></span>
          <span class="min-w-0 flex-1 truncate text-sm">{s.title}</span>
          <span class="text-muted-foreground shrink-0 text-[13px]"
            >{s.status === "running" ? "Running" : "Waiting"} · {s.age}</span
          >
        </a>
      </li>
    {/each}
    <!-- eslint-enable svelte/no-navigation-without-resolve -->
  </ul>
  <p class="text-muted-foreground px-1 pb-1 text-[13px] font-semibold">
    Jobs on your servers
  </p>
  <ul class="flex flex-col gap-1">
    {#each TASKS as t (t.id)}
      <li class="px-2 py-1.5">
        <div class="flex items-center gap-2">
          <span class="min-w-0 flex-1 truncate text-sm">{t.name}</span>
          <span class="text-muted-foreground shrink-0 text-[13px]"
            >{t.where}</span
          >
        </div>
        {#if t.state === "running"}
          <div class="bg-muted mt-1 h-1 overflow-hidden rounded-full">
            <span class="bg-info block h-full" style="width:{t.progress}%"
            ></span>
          </div>
        {:else}
          <p class="text-muted-foreground text-[13px]">
            {t.log[t.log.length - 1]}
          </p>
        {/if}
      </li>
    {/each}
  </ul>
</div>
