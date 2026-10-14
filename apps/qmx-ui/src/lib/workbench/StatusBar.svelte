<script lang="ts">
  import { cn } from "$lib/utils";
  import { resolve } from "$app/paths";
  import Cpu from "@lucide/svelte/icons/cpu";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import EnvChip from "$lib/lab/EnvChip.svelte";
  import { ENVIRONMENTS, RUNS } from "$lib/lab/demo";
  import { workbench, type ConnectionState } from "./workbench.svelte";

  const online = ENVIRONMENTS.filter((e) => e.status !== "offline").length;
  const jobs = (env?: string) =>
    RUNS.filter(
      (r) =>
        (r.status === "running" || r.status === "queued") &&
        (!env || r.env === env),
    ).length;

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

  {#if workbench.demoMode}
    <DropdownMenu.Root>
      <DropdownMenu.Trigger
        class="hover:text-foreground flex h-5 items-center gap-1.5 rounded px-1"
        aria-label="Machines"
      >
        <Cpu class="size-3.5" />{online} of {ENVIRONMENTS.length} machines ·
        {jobs()} jobs
      </DropdownMenu.Trigger>
      <DropdownMenu.Content side="top" align="start" class="w-80">
        <DropdownMenu.Label>Machines (demo)</DropdownMenu.Label>
        {#each ENVIRONMENTS as e (e.id)}
          <DropdownMenu.Item>
            <EnvChip env={e.id} status={jobs(e.id) ? "running" : "done"} />
            <span class="text-muted-foreground ml-auto text-xs"
              >{e.status === "offline" ? "offline" : `${jobs(e.id)} jobs`}</span
            >
          </DropdownMenu.Item>
        {/each}
        <DropdownMenu.Separator />
        <DropdownMenu.Item>
          {#snippet child({ props })}
            <!-- eslint-disable svelte/no-navigation-without-resolve -- resolved path plus a query string -->
            <a {...props} href={`${resolve("/settings")}?tab=servers`}
              >Manage machines</a
            >
            <!-- eslint-enable svelte/no-navigation-without-resolve -->
          {/snippet}
        </DropdownMenu.Item>
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  {/if}
  <span class="ml-auto">QMX UI · daemon wiring pending</span>
</footer>
