<script lang="ts">
  /**
   * Read-only log of a job's output (preview, not a shell). Lines stream
   * from the JobHandle; the demo passes a fixed transcript.
   */
  let {
    lines,
    command,
    status = "done",
  }: {
    lines: string[];
    command?: string;
    status?: "queued" | "running" | "done" | "failed";
  } = $props();

  const TONE = {
    queued: "text-muted-foreground",
    running: "text-info",
    done: "text-success",
    failed: "text-destructive",
  };
</script>

<div
  class="flex h-full min-h-0 flex-col overflow-hidden rounded-lg border bg-black/40 font-mono text-[12.5px]"
>
  {#if command}
    <div class="flex items-center gap-2 border-b px-3 py-1.5">
      <span class="text-muted-foreground">$</span>
      <span class="truncate">{command}</span>
      <span class="ml-auto text-[11px] uppercase {TONE[status]}">{status}</span>
    </div>
  {/if}
  <pre
    class="min-h-0 flex-1 overflow-auto px-3 py-2 leading-relaxed whitespace-pre-wrap"
    role="log"
    aria-live="polite">{lines.join("\n")}</pre>
</div>
