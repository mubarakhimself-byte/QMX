<script lang="ts">
  /** Job state as a dot plus word. `unknown` means contact was lost; it is never shown as failed. */
  import { cn } from "$lib/utils";
  import type { RunStatus } from "./demo";

  let { status, label = true }: { status: RunStatus; label?: boolean } =
    $props();

  const TONE: Record<RunStatus, string> = {
    queued: "bg-muted-foreground/50",
    running: "bg-info animate-pulse motion-reduce:animate-none",
    done: "bg-success",
    failed: "bg-destructive",
    aborted: "bg-warning",
    unknown: "border border-warning bg-transparent",
  };
</script>

<span class="inline-flex items-center gap-1.5 text-xs" title={status}>
  <span class={cn("size-2 shrink-0 rounded-full", TONE[status])}></span>
  {#if label}<span
      class={status === "unknown" ? "text-warning" : "text-muted-foreground"}
      >{status}</span
    >{/if}
</span>
