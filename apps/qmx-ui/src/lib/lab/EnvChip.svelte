<script lang="ts">
  /**
   * Where a job runs. This machine is quiet; anything elsewhere is tinted
   * and pulses while it runs, so off-machine work is never mistaken for
   * local work.
   */
  import Laptop from "@lucide/svelte/icons/laptop";
  import Server from "@lucide/svelte/icons/server";
  import Cloud from "@lucide/svelte/icons/cloud";
  import { cn } from "$lib/utils";
  import { envById, type RunStatus } from "./demo";

  let {
    env,
    status,
    compact = false,
  }: { env: string; status?: RunStatus; compact?: boolean } = $props();

  const e = $derived(envById(env));
  const remote = $derived(e?.kind !== "local");
  const Icon = $derived(
    e?.kind === "local" ? Laptop : e?.kind === "remote_host" ? Server : Cloud,
  );
</script>

<span
  class={cn(
    "inline-flex max-w-full items-center gap-1.5 rounded-md px-1.5 py-0.5 text-xs whitespace-nowrap",
    remote ? "bg-info/12 text-info" : "text-muted-foreground",
  )}
  title={e ? `${e.name} · ${e.where}` : env}
>
  <span
    class={cn(
      "size-1.5 shrink-0 rounded-full",
      remote ? "bg-info" : "bg-muted-foreground",
      remote && status === "running" && "remote-pulse",
    )}
  ></span>
  <Icon class="size-3 shrink-0" />
  {#if !compact}<span class="truncate">{e?.name ?? env}</span>{/if}
</span>
