<script lang="ts">
  /**
   * Where work runs: this machine and every remote host, notebook or GPU
   * provider the operator connects (CT-46 execution environments). Shows load,
   * cost and whether results from there can count as evidence (B-9: sealed and
   * governed data stay on the controlled machine). Anyone can add more.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import EnvChip from "../EnvChip.svelte";
  import { ENVIRONMENTS, RUNS, STORAGE } from "../demo";
  import HardDrive from "@lucide/svelte/icons/hard-drive";

  const ADD = [
    { label: "A server over SSH", note: "Any VPS or box you control" },
    { label: "Google Colab", note: "Notebook runtime with a GPU" },
    { label: "AWS, GCP or Azure", note: "Cloud GPU instances" },
    { label: "RunPod, Lambda, Vast…", note: "GPU marketplaces" },
    { label: "Another QMX machine", note: "Desktop or always-on host" },
  ];
  const STATUS_TONE = {
    ready: "text-success",
    busy: "text-info",
    offline: "text-muted-foreground",
  };
</script>

<div class="flex h-full flex-col">
  <div class="flex h-9 shrink-0 items-center gap-2 border-b px-3 text-xs">
    <span class="text-muted-foreground"
      >{ENVIRONMENTS.filter((e) => e.status !== "offline").length} of {ENVIRONMENTS.length}
      online</span
    >
    <DropdownMenu.Root>
      <DropdownMenu.Trigger>
        {#snippet child({ props })}
          <Button {...props} variant="ghost" size="sm" class="ml-auto h-7"
            ><Plus />Add compute</Button
          >
        {/snippet}
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="end" class="w-64">
        {#each ADD as a (a.label)}
          <DropdownMenu.Item
            onclick={() =>
              workbench.notify(
                `Connecting ${a.label} needs the daemon. Its keys stay in your credential store.`,
              )}
          >
            <span class="flex flex-col">
              <span>{a.label}</span>
              <span class="text-muted-foreground text-xs">{a.note}</span>
            </span>
          </DropdownMenu.Item>
        {/each}
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  </div>
  <ul class="min-h-0 flex-1 overflow-auto">
    {#each ENVIRONMENTS as e (e.id)}
      {@const jobs = RUNS.filter(
        (r) =>
          r.env === e.id && (r.status === "running" || r.status === "queued"),
      )}
      <li class="border-b border-border/50 px-3 py-2.5">
        <div class="flex items-center gap-2">
          <EnvChip env={e.id} status={jobs.length ? "running" : "done"} />
          <span class="text-muted-foreground truncate text-xs">{e.where}</span>
          <span class={cn("ml-auto text-xs", STATUS_TONE[e.status])}
            >{e.status}</span
          >
        </div>
        <div class="mt-1.5 flex items-center gap-2">
          <span class="bg-muted h-1.5 flex-1 overflow-hidden rounded-full">
            <span
              class={cn(
                "block h-full",
                e.kind === "local" ? "bg-primary" : "bg-info",
              )}
              style="width: {(e.slots[0] / e.slots[1]) * 100}%"
            ></span>
          </span>
          <span class="num text-muted-foreground text-xs"
            >{e.slots[0]}/{e.slots[1]} slots</span
          >
        </div>
        <div
          class="text-muted-foreground mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs"
        >
          <span>{e.hardware}</span>
          {#if e.cost}<span class="num">{e.cost}</span>{/if}
          <span class="flex items-center gap-1">
            {#if e.evidence}<ShieldCheck class="text-success size-3" />Can
              produce evidence{:else}<FlaskConical class="size-3" />Exploration
              only{/if}
          </span>
        </div>
        {#if jobs.length}
          <p class="mt-1 text-xs">
            {jobs.length} job{jobs.length > 1 ? "s" : ""}:
            <span class="text-muted-foreground"
              >{jobs
                .map((j) => `${j.procedure} ${j.symbol} ${j.timeframe}`)
                .join(", ")}</span
            >
          </p>
        {/if}
      </li>
    {/each}
  </ul>
  <div class="border-t">
    <div class="flex h-8 items-center px-3 text-xs">
      <span class="font-medium">Storage</span>
      <span class="text-muted-foreground ml-1.5">new scope</span>
      <button
        type="button"
        class="text-muted-foreground hover:text-foreground ml-auto flex items-center gap-1"
        onclick={() =>
          workbench.notify(
            "Connecting a bucket needs the daemon. Keys stay in your credential store.",
          )}><Plus class="size-3.5" />Add storage</button
      >
    </div>
    <ul>
      {#each STORAGE as b (b.id)}
        <li class="flex items-center gap-2 px-3 py-1.5 text-xs">
          <HardDrive class="text-muted-foreground size-3.5" />
          <span class="font-medium">{b.name}</span>
          <span class="text-muted-foreground truncate">{b.where}</span>
          <span
            class="ml-auto whitespace-nowrap {b.status === 'offline'
              ? 'text-muted-foreground'
              : ''}">{b.used}</span
          >
        </li>
      {/each}
    </ul>
  </div>
  <p class="text-muted-foreground border-t px-3 py-2 text-xs">
    Runs elsewhere never see your sealed test data, so their results are for
    exploring. Rerun a winner here to make it evidence.
  </p>
</div>
