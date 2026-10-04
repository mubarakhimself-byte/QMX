<script lang="ts">
  /**
   * Every machine QMX uses, in one place: trading servers (they keep
   * trading when this laptop is off), Lab machines for tests and training,
   * and storage. One card per machine with what it does, its health and
   * its cost; add a VPS, a cloud GPU or Colab from here.
   */
  import Plus from "@lucide/svelte/icons/plus";
  import Server from "@lucide/svelte/icons/server";
  import HardDrive from "@lucide/svelte/icons/hard-drive";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ACCOUNTS, NODES } from "$lib/portfolio/demo";
  import { ENVIRONMENTS, STORAGE } from "$lib/lab/demo";

  const TONE: Record<string, string> = {
    up: "bg-success",
    ready: "bg-success",
    busy: "bg-info",
    degraded: "bg-warning",
    offline: "bg-muted-foreground",
    down: "bg-destructive",
  };
  const need = (what: string) => workbench.notify(`${what} needs the daemon.`);
</script>

<div class="flex flex-col gap-8">
  <section>
    <div class="mb-3 flex items-center gap-3">
      <h3 class="text-lg font-semibold">Trading servers</h3>
      <span class="text-muted-foreground"
        >Keep trading when this laptop is off</span
      >
    </div>
    <div class="grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">
      {#each NODES as n (n.id)}
        <article class="rounded-2xl border p-5">
          <div class="flex items-center gap-2">
            <span class={cn("size-2.5 rounded-full", TONE[n.status])}></span>
            <Server class="text-muted-foreground size-4" />
            <h4 class="font-semibold">{n.name}</h4>
            <span class="text-muted-foreground ml-auto text-sm">{n.status}</span
            >
          </div>
          <p class="text-muted-foreground mt-1">{n.where} · up {n.uptime}</p>
          <p class="mt-3">
            Trades {ACCOUNTS.filter((a) => a.node === n.id)
              .map((a) => a.name)
              .join(", ") || "nothing yet"}
          </p>
          <p class="text-muted-foreground mt-1 text-sm">
            {n.latency.map((l) => `${l.venue} ${l.ms} ms`).join(" · ")} · CPU {n.cpu}%
          </p>
          <div class="mt-4 flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onclick={() => need(`Opening ${n.name}`)}>Manage</Button
            >
            <Button
              size="sm"
              variant="ghost"
              onclick={() => need(`Testing ${n.name}`)}>Test latency</Button
            >
          </div>
        </article>
      {/each}
    </div>
  </section>

  <section>
    <div class="mb-3 flex items-center gap-3">
      <h3 class="text-lg font-semibold">Lab machines</h3>
      <span class="text-muted-foreground"
        >Where tests, sweeps and training run</span
      >
    </div>
    <div class="grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">
      {#each ENVIRONMENTS as e (e.id)}
        <article class="rounded-2xl border p-5">
          <div class="flex items-center gap-2">
            <span class={cn("size-2.5 rounded-full", TONE[e.status])}></span>
            <h4 class="font-semibold">{e.name}</h4>
            <span class="text-muted-foreground ml-auto text-sm">{e.status}</span
            >
          </div>
          <p class="text-muted-foreground mt-1">{e.where}</p>
          <p class="mt-3">{e.hardware}</p>
          <p class="text-muted-foreground mt-1 text-sm">
            {e.slots[0]} of {e.slots[1]} job slots busy{e.evidence
              ? " · runs here count as evidence"
              : ""}
          </p>
        </article>
      {/each}
    </div>
  </section>

  <section>
    <div class="mb-3 flex items-center gap-3">
      <h3 class="text-lg font-semibold">Storage</h3>
      <span class="text-muted-foreground">Data, models and reports</span>
    </div>
    <div class="grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">
      {#each STORAGE as s (s.id)}
        <article class="flex items-start gap-3 rounded-2xl border p-5">
          <HardDrive class="text-muted-foreground mt-0.5 size-5" />
          <div>
            <h4 class="font-semibold">{s.name}</h4>
            <p class="text-muted-foreground">{s.where} · {s.used}</p>
          </div>
        </article>
      {/each}
    </div>
  </section>

  <DropdownMenu.Root>
    <DropdownMenu.Trigger>
      {#snippet child({ props })}
        <Button {...props} variant="outline" class="w-fit"
          ><Plus />Add a machine</Button
        >
      {/snippet}
    </DropdownMenu.Trigger>
    <DropdownMenu.Content class="w-72">
      <DropdownMenu.Item onclick={() => need("Adding a VPS over SSH")}
        >A VPS (over SSH)</DropdownMenu.Item
      >
      <DropdownMenu.Item onclick={() => need("Adding a cloud GPU")}
        >A cloud GPU (AWS, RunPod…)</DropdownMenu.Item
      >
      <DropdownMenu.Item onclick={() => need("Connecting Colab")}
        >Google Colab</DropdownMenu.Item
      >
      <DropdownMenu.Item onclick={() => need("Adding a storage bucket")}
        >A storage bucket</DropdownMenu.Item
      >
    </DropdownMenu.Content>
  </DropdownMenu.Root>
</div>
