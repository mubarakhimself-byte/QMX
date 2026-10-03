<script lang="ts">
  /**
   * Which machine the Lab is looking at, like a remote window in VS Code.
   * "All machines" shows everything; picking one connects first (reachable,
   * signed in, healthy) and then every tile shows only that machine's work.
   * Runs started from the header go to the chosen machine, or this laptop
   * when looking at all of them.
   */
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Check from "@lucide/svelte/icons/check";
  import Layers from "@lucide/svelte/icons/layers";
  import Settings2 from "@lucide/svelte/icons/settings-2";
  import { resolve } from "$app/paths";
  import { goto } from "$app/navigation";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import EnvChip from "./EnvChip.svelte";
  import { ENVIRONMENTS, RUNS } from "./demo";
  import { lab } from "./lab.svelte";

  const jobs = (env: string) =>
    RUNS.filter(
      (r) => r.env === env && (r.status === "running" || r.status === "queued"),
    ).length;
</script>

<DropdownMenu.Root>
  <DropdownMenu.Trigger>
    {#snippet child({ props })}
      <Button
        {...props}
        variant="outline"
        size="sm"
        class={cn("gap-1.5", lab.machine && "border-info/50")}
        aria-label="Choose the machine to look at"
      >
        {#if lab.machine}
          <EnvChip env={lab.machine} status="running" />
        {:else}
          <Layers class="size-3.5" />All machines
        {/if}
        <ChevronDown class="size-3.5" />
      </Button>
    {/snippet}
  </DropdownMenu.Trigger>
  <DropdownMenu.Content align="end" class="w-80">
    <DropdownMenu.Label>Look at</DropdownMenu.Label>
    <DropdownMenu.Item onclick={() => lab.connect(null)}>
      <Layers />
      <span class="flex flex-1 flex-col">
        <span>All machines</span>
        <span class="text-muted-foreground text-xs"
          >Everything, wherever it runs. Runs start on this laptop.</span
        >
      </span>
      {#if !lab.machine}<Check class="size-4" />{/if}
    </DropdownMenu.Item>
    <DropdownMenu.Separator />
    {#each ENVIRONMENTS as e (e.id)}
      <DropdownMenu.Item onclick={() => lab.connect(e.id)}>
        <span class="flex w-full flex-col gap-0.5">
          <span class="flex items-center gap-2">
            <EnvChip env={e.id} status={jobs(e.id) ? "running" : "done"} />
            <span class="text-muted-foreground ml-auto text-xs"
              >{e.status === "offline"
                ? "offline"
                : `${jobs(e.id)} job${jobs(e.id) === 1 ? "" : "s"}`}</span
            >
            {#if lab.machine === e.id}<Check class="size-4" />{/if}
          </span>
          <span class="text-muted-foreground text-xs"
            >{e.where} · {e.hardware}{e.evidence
              ? ""
              : " · exploration only"}</span
          >
        </span>
      </DropdownMenu.Item>
    {/each}
    <DropdownMenu.Separator />
    <DropdownMenu.Item
      onclick={() =>
        // eslint-disable-next-line svelte/no-navigation-without-resolve -- resolved path plus a query string
        goto(`${resolve("/settings")}?tab=compute`)}
      ><Settings2 />Add or manage machines</DropdownMenu.Item
    >
  </DropdownMenu.Content>
</DropdownMenu.Root>
