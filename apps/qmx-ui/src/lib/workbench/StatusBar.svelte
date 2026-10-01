<script lang="ts">
  import { cn } from "$lib/utils";
  import { workbench, type ConnectionState } from "./workbench.svelte";

  const LABEL: Record<ConnectionState, string> = {
    "not-bound": "Not connected to daemon",
    connecting: "Connecting…",
    connected: "Connected",
    reconnecting: "Reconnecting…",
    failed: "Connection failed",
  };
</script>

<footer
  class="bg-sidebar border-sidebar-border text-muted-foreground flex h-7 shrink-0 items-center gap-3 border-t px-3 text-xs"
>
  <span class="flex items-center gap-1.5" role="status">
    <span
      class={cn(
        "size-2 rounded-full",
        workbench.connection === "connected" && "bg-success",
        workbench.connection === "reconnecting" && "bg-warning",
        workbench.connection === "connecting" && "bg-warning",
        workbench.connection === "failed" && "bg-destructive",
        workbench.connection === "not-bound" &&
          "border-muted-foreground border",
      )}
      aria-hidden="true"
    ></span>
    {LABEL[workbench.connection]}
  </span>

  <span class="ml-auto">QMX UI · daemon wiring pending</span>
</footer>
